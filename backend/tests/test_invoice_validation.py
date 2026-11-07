
from services.invoice_validation import validate_invoice_data


def sample_invoice():
    return {
        "supplier_name": "CONTOSO LTD.",
        "supplier_tax_id": None,
        "invoice_number": "INV-100",
        "invoice_date": "2019-11-15",
        "subtotal": 100.0,
        "tax": 10.0,
        "total": 110.0,
        "currency": "USD",
        "confidence": {
            "VendorName": 0.936,
            "InvoiceTotal": 0.93,
        },
    }


def test_correct_amounts():
    result = validate_invoice_data(sample_invoice())

    assert result["financial_validation"]["is_consistent"] is True
    assert result["financial_validation"]["difference"] == "0.0"


def test_incorrect_amounts():
    invoice = sample_invoice()
    invoice["total"] = 150.0

    result = validate_invoice_data(invoice)

    assert result["financial_validation"]["is_consistent"] is False
    assert any(
        finding["type"] == "financial_mismatch"
        for finding in result["findings"]
    )


def test_missing_supplier_tax_id():
    result = validate_invoice_data(sample_invoice())

    assert any(
        finding["field"] == "supplier_tax_id"
        for finding in result["findings"]
    )


def test_missing_total():
    invoice = sample_invoice()
    invoice["total"] = None

    result = validate_invoice_data(invoice)

    assert result["financial_validation"]["is_consistent"] is None
    assert result["requires_human_review"] is True


def test_low_confidence():
    invoice = sample_invoice()
    invoice["confidence"]["InvoiceTotal"] = 0.55

    result = validate_invoice_data(invoice)

    assert any(
        finding["type"] == "low_confidence"
        for finding in result["findings"]
    )


def test_no_automatic_approval():
    invoice = sample_invoice()
    invoice["supplier_tax_id"] = "DEMO123456"

    result = validate_invoice_data(invoice)

    assert result["recommended_status"] == "pending_review"
