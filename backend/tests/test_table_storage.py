"""Contrato del adaptador Table Storage sin conexiones a Azure."""

import copy
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from azure.core.exceptions import HttpResponseError

from database import table_storage
from database.connection import get_connection, initialize_database, storage_backend
from repositories.business_data import get_branch_report, get_inventory, get_order
from repositories.invoices import get_invoice, get_invoice_stats, list_invoices
from repositories.invoice_analyses import get_saved_invoice_analysis
from repositories.invoice_reviews import list_invoice_reviews
from repositories.complaints import create_complaint, get_complaint
from seed_business_demo import seed_business_demo_data
from seed_demo import seed_demo_data
from services.ai_quota import QuotaExceededError, get_quota_status, reserve_ai_request
from services.invoice_duplicates import DuplicateDocumentError, DuplicateBusinessError, claim_document
from services.invoice_review import review_invoice, InvoiceAlreadyReviewedError
from services import invoice_pipeline as pipeline
from scripts.migrate_sqlite_to_tables import migrate


class FakeEntity(dict):
    def __init__(self, values, version):
        super().__init__(values)
        self.metadata = {"etag": str(version)}


class FakeTable:
    def __init__(self):
        self.rows = {}
        self.lock = threading.Lock()
        self.version = 0

    def query_entities(self, query_filter):
        assert query_filter == "PartitionKey eq 'demo'"
        with self.lock:
            return [FakeEntity(copy.deepcopy(row), version)
                    for row, version in self.rows.values()]

    def submit_transaction(self, operations):
        with self.lock:
            for item in operations:
                action, entity = item[:2]
                key = (entity["PartitionKey"], entity["RowKey"])
                old = self.rows.get(key)
                if action == "create" and old is not None:
                    error = HttpResponseError("duplicate")
                    error.status_code = 409
                    raise error
                if action in ("update", "delete") and (old is None or
                        str(old[1]) != item[2]["etag"]):
                    error = HttpResponseError("stale etag")
                    error.status_code = 412
                    raise error
            for item in operations:
                action, entity = item[:2]
                key = (entity["PartitionKey"], entity["RowKey"])
                if action == "delete":
                    del self.rows[key]
                else:
                    self.version += 1
                    self.rows[key] = (copy.deepcopy(entity), self.version)


@pytest.fixture
def table_backend(monkeypatch):
    fake = FakeTable()
    monkeypatch.setenv("STORAGE_BACKEND", "table")
    monkeypatch.setenv("AZURE_TABLE_ACCOUNT_URL", "https://example.table.core.windows.net")
    monkeypatch.setenv("PROD_MAX_DAILY_ASSISTANT_QUESTIONS", "2")
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Production")
    monkeypatch.setenv("WEBSITE_INSTANCE_ID", "test-instance")
    monkeypatch.setattr(table_storage, "get_table_client", lambda: fake)
    return fake


def test_seed_reads_and_persistence_after_new_connection(table_backend):
    seed_demo_data()
    seed_business_demo_data()
    count = len(table_backend.rows)
    seed_demo_data()
    seed_business_demo_data()
    assert len(table_backend.rows) == count
    assert len(list_invoices()) == 4
    assert get_invoice_stats()["pending_review"] == 2
    assert get_order("PED-001")["branch_name"] == "León"
    assert get_inventory("Cloro 1L", "León")["inventory"][0]["quantity"] == 42
    assert len(get_branch_report()["branches"]) == 5
    with get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM policies").fetchone()[0] == 2


def test_review_and_quota_are_persistent(table_backend):
    seed_demo_data()
    result = review_invoice("factura-003", "approve", "demo-reviewer")
    assert result["status"] == "validated"
    assert get_invoice("factura-003")["status"] == "validated"
    assert list_invoice_reviews("factura-003")["total"] == 1
    reserve_ai_request("assistant", "MAX_DAILY_ASSISTANT_QUESTIONS", "ENABLE_ASSISTANT")
    assert get_quota_status("assistant")["remaining"] == 1
    reserve_ai_request("assistant", "MAX_DAILY_ASSISTANT_QUESTIONS", "ENABLE_ASSISTANT")
    with pytest.raises(QuotaExceededError):
        reserve_ai_request("assistant", "MAX_DAILY_ASSISTANT_QUESTIONS", "ENABLE_ASSISTANT")


def test_concurrent_reservations_and_claims(table_backend):
    with ThreadPoolExecutor(max_workers=6) as executor:
        outcomes = list(executor.map(lambda _: _reserve_result(), range(6)))
    assert outcomes.count("ok") == 2
    assert outcomes.count("limited") == 4
    assert get_quota_status("assistant")["remaining"] == 0

    with ThreadPoolExecutor(max_workers=2) as executor:
        claims = list(executor.map(lambda _: _claim_result(), range(2)))
    assert claims.count("ok") == 1
    assert claims.count("duplicate") == 1


def test_invoice_pipeline_analysis_and_complaint(table_backend, monkeypatch):
    seed_business_demo_data()
    monkeypatch.setenv("PROD_MAX_DAILY_INVOICE_ANALYSES", "2")
    monkeypatch.setattr(pipeline, "extract_invoice", lambda _: {
        "supplier_name": "Proveedor Ficticio", "supplier_tax_id": None,
        "invoice_number": "TEST-100", "invoice_date": "2026-11-07",
        "subtotal": 100.0, "tax": 16.0, "total": 116.0,
        "currency": "MXN", "confidence": {},
    })
    monkeypatch.setattr(pipeline, "analyze_invoice_with_ai", lambda _: {
        "invoice_number": "TEST-100", "financial_validation": {"is_consistent": True},
        "findings": [], "recommended_status": "pending_review",
        "requires_human_review": True,
        "ai_analysis": {"summary": "Revisión ficticia", "review_steps": []},
    })
    result = pipeline.analyze_and_save_invoice(b"%PDF-1.4 test document")
    assert get_invoice(result["invoice_id"])["total"] == 116.0
    assert get_saved_invoice_analysis(result["invoice_id"])["analysis"]["ai_analysis"]["summary"] == "Revisión ficticia"
    assert get_quota_status("invoice_analysis")["remaining"] == 1
    complaint = create_complaint("PED-001", "LEO", "Entrega ficticia incompleta", "delivery")
    assert get_complaint(complaint["folio"])["status"] == "open"


def test_concurrent_review_writes_one_audit_record(table_backend):
    seed_demo_data()
    def attempt(_):
        try:
            review_invoice("factura-003", "approve", "demo-reviewer")
            return "ok"
        except InvoiceAlreadyReviewedError:
            return "already"
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(attempt, range(2)))
    assert sorted(outcomes) == ["already", "ok"]
    assert list_invoice_reviews("factura-003")["total"] == 1


def test_two_different_files_cannot_create_same_business_invoice(table_backend, monkeypatch):
    monkeypatch.setenv("PROD_MAX_DAILY_INVOICE_ANALYSES", "2")
    monkeypatch.setattr(pipeline, "extract_invoice", lambda _: {
        "supplier_name": "Proveedor Demo", "supplier_tax_id": "RFC-1",
        "invoice_number": "X-100", "invoice_date": "2026-11-07",
        "subtotal": 100.0, "tax": 16.0, "total": 116.0,
        "currency": "MXN", "confidence": {},
    })
    monkeypatch.setattr(pipeline, "analyze_invoice_with_ai", lambda _: {
        "invoice_number": "X-100", "financial_validation": {"is_consistent": True},
        "findings": [], "recommended_status": "pending_review",
        "requires_human_review": True,
        "ai_analysis": {"summary": "Prueba", "review_steps": []},
    })
    def attempt(index):
        try:
            pipeline.analyze_and_save_invoice(f"%PDF-1.4 file-{index}".encode())
            return "ok"
        except DuplicateBusinessError:
            return "duplicate"
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(attempt, range(2)))
    assert sorted(outcomes) == ["duplicate", "ok"]
    assert get_invoice_stats()["total_invoices"] == 1


def test_migration_preserves_all_rows_and_is_idempotent(table_backend, monkeypatch, tmp_path):
    source = tmp_path / "source.db"
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("SQLITE_DB_PATH", str(source))
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    seed_demo_data()
    seed_business_demo_data()
    monkeypatch.setenv("STORAGE_BACKEND", "table")
    monkeypatch.setenv("WEBSITE_INSTANCE_ID", "test-instance")
    created, existing = migrate(source, table_backend)
    assert created > 0 and existing == 0
    assert migrate(source, table_backend) == (0, created)
    assert get_invoice_stats()["total_invoices"] == 4


def test_azure_runtime_rejects_sqlite(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("WEBSITE_INSTANCE_ID", "test-instance")
    with pytest.raises(RuntimeError, match="no es persistente"):
        storage_backend()


def test_evaluator_login_preserves_existing_table_entities(table_backend, monkeypatch):
    import hashlib
    from security.evaluator_auth import login, logout

    seed_demo_data()
    before = {key: copy.deepcopy(value[0]) for key, value in table_backend.rows.items()}
    salt = bytes.fromhex("cd" * 16)
    monkeypatch.setenv("EVALUATOR_ACCESS_ENABLED", "true")
    monkeypatch.setenv("EVALUATOR_CODE_SALT", salt.hex())
    monkeypatch.setenv("EVALUATOR_CODE_HASH", hashlib.pbkdf2_hmac("sha256", b"private-code", salt, 210_000).hex())
    token, _ = login("private-code")
    logout(token)
    for key, original in before.items():
        assert table_backend.rows[key][0] == original


def _reserve_result():
    try:
        reserve_ai_request("assistant", "MAX_DAILY_ASSISTANT_QUESTIONS", "ENABLE_ASSISTANT")
        return "ok"
    except QuotaExceededError:
        return "limited"


def _claim_result():
    try:
        claim_document("a" * 64)
        return "ok"
    except DuplicateDocumentError:
        return "duplicate"
