from concurrent.futures import ThreadPoolExecutor
from threading import Event

import pytest

from database.connection import get_connection, initialize_database
from services import invoice_pipeline as pipeline
from services.invoice_duplicates import (
    DuplicateBusinessError,
    DuplicateDocumentError,
    find_business_duplicate,
)


@pytest.fixture
def invoice_data(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "duplicates.db"))
    initialize_database()
    extraction = {
        "supplier_name": "Proveedor Demo",
        "supplier_tax_id": "RFC123",
        "invoice_number": "INV-100",
        "invoice_date": "2026-11-01",
        "subtotal": 100.0,
        "tax": 16.0,
        "total": 116.0,
        "currency": "MXN",
        "confidence": {},
    }
    monkeypatch.setattr(pipeline, "extract_invoice", lambda _: dict(extraction))
    monkeypatch.setattr(pipeline, "analyze_invoice_with_ai", lambda _: {
        "invoice_number": extraction["invoice_number"],
        "financial_validation": {"is_consistent": True},
        "findings": [],
        "requires_human_review": True,
        "recommended_status": "pending_review",
        "ai_analysis": {"summary": "Revisar.", "review_steps": []},
    })
    return extraction


def test_identical_document_skips_second_azure_call(invoice_data, monkeypatch):
    first = pipeline.analyze_and_save_invoice(b"%PDF-1.4 same")
    monkeypatch.setattr(pipeline, "extract_invoice", lambda _: pytest.fail("Azure fue llamado"))

    with pytest.raises(DuplicateDocumentError) as error:
        pipeline.analyze_and_save_invoice(b"%PDF-1.4 same")

    assert error.value.invoice_id == first["invoice_id"]


def test_same_invoice_in_pdf_and_image_is_confirmed(invoice_data, monkeypatch):
    first = pipeline.analyze_and_save_invoice(b"%PDF-1.4 original")
    monkeypatch.setattr(pipeline, "analyze_invoice_with_ai", lambda _: pytest.fail("OpenAI fue llamado"))

    with pytest.raises(DuplicateBusinessError) as error:
        pipeline.analyze_and_save_invoice(b"\x89PNG\r\n\x1a\nother")

    assert error.value.related_invoice_id == first["invoice_id"]


def test_same_number_different_supplier_is_not_duplicate(invoice_data):
    pipeline.analyze_and_save_invoice(b"%PDF-1.4 first")
    candidate = dict(invoice_data, supplier_name="Otro proveedor")

    assert find_business_duplicate(candidate)["status"] == "none"


def test_same_supplier_amount_different_number_is_possible(invoice_data):
    first = pipeline.analyze_and_save_invoice(b"%PDF-1.4 first")
    candidate = dict(invoice_data, invoice_number="INV-200")

    result = find_business_duplicate(candidate)

    assert result["status"] == "possible"
    assert result["related_invoices"][0]["invoice_id"] == first["invoice_id"]


def test_missing_number_is_not_evaluable(invoice_data):
    candidate = dict(invoice_data, invoice_number=None)

    assert find_business_duplicate(candidate)["status"] == "not_evaluable"


def test_missing_date_does_not_confirm_duplicate(invoice_data):
    pipeline.analyze_and_save_invoice(b"%PDF-1.4 original")
    candidate = dict(invoice_data, invoice_date=None)

    assert find_business_duplicate(candidate)["status"] == "possible"


def test_failed_analysis_releases_hash(invoice_data, monkeypatch):
    monkeypatch.setattr(pipeline, "extract_invoice", lambda _: (_ for _ in ()).throw(RuntimeError("Azure failed")))

    with pytest.raises(RuntimeError):
        pipeline.analyze_and_save_invoice(b"%PDF-1.4 failure")

    with get_connection() as connection:
        count = connection.execute("SELECT COUNT(*) FROM invoice_document_claims").fetchone()[0]
    assert count == 0


def test_concurrent_identical_requests_are_serialized(invoice_data, monkeypatch):
    entered = Event()
    proceed = Event()

    def slow_extract(_):
        entered.set()
        assert proceed.wait(5)
        return dict(invoice_data)

    monkeypatch.setattr(pipeline, "extract_invoice", slow_extract)

    with ThreadPoolExecutor(max_workers=2) as executor:
        first = executor.submit(pipeline.analyze_and_save_invoice, b"%PDF-1.4 same document")
        assert entered.wait(5)
        second = executor.submit(pipeline.analyze_and_save_invoice, b"%PDF-1.4 same document")
        with pytest.raises(DuplicateDocumentError):
            second.result(timeout=5)
        proceed.set()
        assert first.result(timeout=5)["invoice_id"]
