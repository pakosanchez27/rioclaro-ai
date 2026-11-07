
import json

import pytest

from database.connection import (
    get_connection,
    initialize_database,
)
from repositories.invoices import get_invoice
from services import invoice_pipeline as pipeline


@pytest.fixture
def demo_database(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "SQLITE_DB_PATH",
        str(tmp_path / "pipeline_test.db"),
    )

    extraction = {
        "supplier_name": "CONTOSO LTD.",
        "supplier_tax_id": None,
        "invoice_number": "INV-100",
        "invoice_date": "2019-11-15",
        "subtotal": 100.0,
        "tax": 10.0,
        "total": 110.0,
        "currency": "USD",
        "confidence": {},
    }

    def fake_extract(document_bytes):
        assert document_bytes
        return dict(extraction)

    def fake_analyze(invoice):
        return {
            "invoice_number": invoice["invoice_number"],
            "financial_validation": {
                "is_consistent": True,
            },
            "findings": [],
            "recommended_status": "pending_review",
            "requires_human_review": True,
            "ai_analysis": {
                "summary": "Factura revisada.",
                "review_steps": [],
            },
        }

    monkeypatch.setattr(
        pipeline,
        "extract_invoice",
        fake_extract,
    )
    monkeypatch.setattr(
        pipeline,
        "analyze_invoice_with_ai",
        fake_analyze,
    )

    return extraction


def test_invoice_is_saved(demo_database):
    result = pipeline.analyze_and_save_invoice(
        b"%PDF-1.4\nexample"
    )

    invoice = get_invoice(result["invoice_id"])

    assert invoice is not None
    assert invoice["supplier_name"] == "CONTOSO LTD."
    assert invoice["total"] == 110.0


def test_invoice_remains_pending(demo_database):
    result = pipeline.analyze_and_save_invoice(
        b"%PDF-1.4\nexample"
    )

    assert result["status"] == "pending_review"


def test_analysis_is_persisted(demo_database):
    result = pipeline.analyze_and_save_invoice(
        b"%PDF-1.4\nexample"
    )

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT extraction_json, analysis_json
            FROM invoice_analyses
            WHERE invoice_id = ?
            """,
            (result["invoice_id"],),
        ).fetchone()

    assert row is not None

    extraction = json.loads(row["extraction_json"])
    analysis = json.loads(row["analysis_json"])

    assert extraction["invoice_number"] == "INV-100"
    assert analysis["ai_analysis"]["summary"] == (
        "Factura revisada."
    )



def test_missing_amount_is_not_saved(
    demo_database, monkeypatch
):
    # Preparar las tablas antes de comprobar
    # que una factura invalida no se guarde.
    initialize_database()

    broken = dict(demo_database)
    broken["total"] = None

    monkeypatch.setattr(
        pipeline,
        "extract_invoice",
        lambda _: broken,
    )

    # El sistema debe rechazar la factura
    # porque falta un importe obligatorio.
    with pytest.raises(pipeline.IncompleteInvoiceError):
        pipeline.analyze_and_save_invoice(b"%PDF-1.4\ninvalid amounts")

    # Comprobar que no se guardo ninguna factura.
    with get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM invoices"
        ).fetchone()[0]

    assert count == 0
