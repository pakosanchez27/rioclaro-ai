
import os
from datetime import date

from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeDocumentRequest


MODEL_ID = "prebuilt-invoice"
MAX_DOCUMENT_BYTES = 4_000_000


class DocumentValidationError(ValueError):
    pass


class InvoiceExtractionError(Exception):
    pass


def _value(obj, snake_name, camel_name=None):
    if obj is None:
        return None

    if isinstance(obj, dict):
        result = obj.get(snake_name)
        if result is None and camel_name:
            result = obj.get(camel_name)
        return result

    return getattr(obj, snake_name, None)


def _field(fields, name):
    return fields.get(name) if fields else None


def _text(fields, name):
    field = _field(fields, name)
    value = _value(field, "value_string", "valueString")
    return value if isinstance(value, str) else None


def _date(fields, name):
    field = _field(fields, name)
    value = _value(field, "value_date", "valueDate")

    if isinstance(value, date):
        return value.isoformat()

    return str(value) if value is not None else None


def _money(fields, name):
    field = _field(fields, name)
    currency = _value(
        field, "value_currency", "valueCurrency"
    )

    amount = _value(currency, "amount")
    code = _value(
        currency, "currency_code", "currencyCode"
    )

    return amount, code


def normalize_invoice(result):
    documents = result.documents or []

    if not documents:
        raise InvoiceExtractionError(
            "No se detectaron datos de una factura."
        )

    fields = documents[0].fields or {}

    subtotal, subtotal_currency = _money(
        fields, "SubTotal"
    )
    tax, tax_currency = _money(
        fields, "TotalTax"
    )
    total, total_currency = _money(
        fields, "InvoiceTotal"
    )

    field_names = [
        "VendorName",
        "VendorTaxId",
        "InvoiceId",
        "InvoiceDate",
        "SubTotal",
        "TotalTax",
        "InvoiceTotal",
    ]

    confidence = {}

    for name in field_names:
        field = _field(fields, name)
        value = _value(field, "confidence")

        confidence[name] = (
            round(float(value), 3)
            if isinstance(value, (int, float))
            else None
        )

    return {
        "supplier_name": _text(fields, "VendorName"),
        "supplier_tax_id": _text(fields, "VendorTaxId"),
        "invoice_number": _text(fields, "InvoiceId"),
        "invoice_date": _date(fields, "InvoiceDate"),
        "subtotal": subtotal,
        "tax": tax,
        "total": total,
        "currency": (
            total_currency
            or subtotal_currency
            or tax_currency
        ),
        "confidence": confidence,
        "metadata": {
            "model": MODEL_ID,
            "pages_analyzed": len(result.pages or []),
            "limited_to_first_page": True,
        },
    }


def validate_document_bytes(document_bytes: bytes) -> None:
    if not isinstance(document_bytes, bytes):
        raise DocumentValidationError(
            "El documento debe enviarse como bytes."
        )

    if not document_bytes:
        raise DocumentValidationError(
            "El documento esta vacio."
        )

    if len(document_bytes) > MAX_DOCUMENT_BYTES:
        raise DocumentValidationError(
            "El documento supera el limite de 4 MB."
        )

    supported = (
        document_bytes.startswith(b"%PDF-")
        or document_bytes.startswith(b"\x89PNG\r\n\x1a\n")
        or document_bytes.startswith(b"\xff\xd8\xff")
    )

    if not supported:
        raise DocumentValidationError(
            "Formato no admitido. Usa PDF, PNG o JPEG."
        )


def extract_invoice(document_bytes: bytes):
    validate_document_bytes(document_bytes)

    endpoint = os.getenv("DOCUMENTINTELLIGENCE_ENDPOINT")
    api_key = os.getenv("DOCUMENTINTELLIGENCE_API_KEY")

    if not endpoint or not api_key:
        raise RuntimeError(
            "Document Intelligence no esta configurado."
        )

    client = DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key),
    )

    poller = client.begin_analyze_document(
        MODEL_ID,
        AnalyzeDocumentRequest(
            bytes_source=document_bytes
        ),
        pages="1",
    )

    result = poller.result()

    return normalize_invoice(result)
