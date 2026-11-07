
from datetime import date
from types import SimpleNamespace as NS

import pytest

from services import document_intelligence as di


def test_normalize_invoice():
    fields = {
        "VendorName": NS(
            value_string="Proveedor Demo",
            confidence=0.98,
        ),
        "InvoiceId": NS(
            value_string="FAC-001",
            confidence=0.97,
        ),
        "InvoiceDate": NS(
            value_date=date(2026, 11, 1),
            confidence=0.96,
        ),
        "InvoiceTotal": NS(
            value_currency=NS(
                amount=1160.00,
                currency_code="MXN",
            ),
            confidence=0.99,
        ),
    }

    result = NS(
        documents=[NS(fields=fields)],
        pages=[NS(page_number=1)],
    )

    invoice = di.normalize_invoice(result)

    assert invoice["supplier_name"] == "Proveedor Demo"
    assert invoice["invoice_number"] == "FAC-001"
    assert invoice["invoice_date"] == "2026-11-01"
    assert invoice["total"] == 1160.00
    assert invoice["currency"] == "MXN"
    assert invoice["tax"] is None
    assert invoice["confidence"]["VendorName"] == 0.98


def test_no_invoice_detected():
    result = NS(documents=[], pages=[])

    with pytest.raises(di.InvoiceExtractionError):
        di.normalize_invoice(result)


def test_invalid_file():
    with pytest.raises(di.DocumentValidationError):
        di.extract_invoice(b"archivo no valido")


def test_empty_file():
    with pytest.raises(di.DocumentValidationError):
        di.extract_invoice(b"")


def test_missing_configuration(monkeypatch):
    monkeypatch.delenv(
        "DOCUMENTINTELLIGENCE_ENDPOINT",
        raising=False,
    )
    monkeypatch.delenv(
        "DOCUMENTINTELLIGENCE_API_KEY",
        raising=False,
    )

    with pytest.raises(RuntimeError):
        di.extract_invoice(b"%PDF-1.4\nfake")


def test_sdk_invocation(monkeypatch):
    monkeypatch.setenv(
        "DOCUMENTINTELLIGENCE_ENDPOINT",
        "https://example.cognitiveservices.azure.com/",
    )
    monkeypatch.setenv(
        "DOCUMENTINTELLIGENCE_API_KEY",
        "fake-key-for-unit-test",
    )

    calls = {}

    class FakeClient:
        def begin_analyze_document(
            self, model_id, request, **kwargs
        ):
            calls["model"] = model_id
            calls["pages"] = kwargs.get("pages")
            calls["request"] = request

            result = NS(
                documents=[NS(fields={})],
                pages=[NS(page_number=1)],
            )

            return NS(result=lambda: result)

    monkeypatch.setattr(
        di,
        "DocumentIntelligenceClient",
        lambda **kwargs: FakeClient(),
    )

    result = di.extract_invoice(b"%PDF-1.4\nfake")

    assert calls["model"] == "prebuilt-invoice"
    assert calls["pages"] == "1"
    assert result["supplier_name"] is None
    assert result["metadata"]["pages_analyzed"] == 1
