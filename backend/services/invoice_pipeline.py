
import json
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

from database.connection import (
    get_connection,
    initialize_database,
)
from services.document_intelligence import extract_invoice, validate_document_bytes
from services.azure_openai import analyze_invoice_with_ai
from services.invoice_duplicates import (
    document_hash,
    claim_document,
    release_document,
    complete_document,
    claim_business_invoice,
    complete_business_invoice,
    release_business_claim,
    find_business_duplicate,
    DuplicateBusinessError,
)
from services.ai_quota import reserve_ai_request


class IncompleteInvoiceError(ValueError):
    pass


def _required_amount(invoice: dict, field: str) -> float:
    value = invoice.get(field)

    if value is None or isinstance(value, bool):
        raise IncompleteInvoiceError(
            f"No se identifico el importe: {field}"
        )

    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise IncompleteInvoiceError(
            f"El importe {field} no es valido"
        )

    if not number.is_finite() or number < 0:
        raise IncompleteInvoiceError(
            f"El importe {field} no es valido"
        )

    return float(number)


def _process_claimed_invoice(document_bytes: bytes, sha256: str) -> dict:
    # 1. Extraer datos mediante Document Intelligence.
    extraction = extract_invoice(document_bytes)

    # 2. Comprobar los valores necesarios para nuestra
    # estructura SQLite actual. Nunca sustituir un dato
    # faltante por cero sin avisar.
    supplier_name = extraction.get("supplier_name")
    currency = extraction.get("currency")

    if (
        not isinstance(supplier_name, str)
        or not supplier_name.strip()
    ):
        raise IncompleteInvoiceError(
            "No se identifico el proveedor."
        )

    if (
        not isinstance(currency, str)
        or len(currency.strip()) != 3
    ):
        raise IncompleteInvoiceError(
            "No se identifico una moneda valida."
        )

    subtotal = _required_amount(extraction, "subtotal")
    tax = _required_amount(extraction, "tax")
    total = _required_amount(extraction, "total")

    duplicate_check = find_business_duplicate(extraction)
    if duplicate_check["status"] == "confirmed":
        raise DuplicateBusinessError(
            duplicate_check["related_invoices"][0]["invoice_id"]
        )

    business_claim_key = claim_business_invoice(extraction, sha256)

    # 3. Ejecutar validaciones financieras y Azure OpenAI.
    analysis = analyze_invoice_with_ai(extraction)
    analysis["duplicate_check"] = duplicate_check
    if duplicate_check["status"] == "possible":
        analysis["findings"].append({
            "type": "possible_duplicate",
            "severity": "high",
            "field": "invoice_number",
            "message": "Posible factura duplicada; revisa las facturas relacionadas.",
        })

    # 4. Generar identificadores y fechas.
    invoice_id = str(uuid.uuid4())
    created_at = datetime.now(
        timezone.utc
    ).isoformat().replace("+00:00", "Z")

    status = "pending_review"

    # 5. Guardar factura, analisis y hash en una transaccion.
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO invoices (
                id,
                supplier_name,
                supplier_tax_id,
                invoice_number,
                invoice_date,
                currency,
                subtotal,
                tax,
                total,
                status,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                invoice_id,
                supplier_name.strip(),
                extraction.get("supplier_tax_id"),
                extraction.get("invoice_number"),
                extraction.get("invoice_date"),
                currency.strip().upper(),
                subtotal,
                tax,
                total,
                status,
                created_at,
                created_at,
            ),
        )

        complete_document(connection, sha256, invoice_id)
        complete_business_invoice(connection, business_claim_key, invoice_id)

        connection.execute(
            """
            INSERT INTO invoice_analyses (
                invoice_id,
                extraction_json,
                analysis_json,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                invoice_id,
                json.dumps(
                    extraction,
                    ensure_ascii=False,
                    allow_nan=False,
                ),
                json.dumps(
                    analysis,
                    ensure_ascii=False,
                    allow_nan=False,
                ),
                created_at,
            ),
        )

    return {
        "invoice_id": invoice_id,
        "status": status,
        "extraction": extraction,
        "analysis": analysis,
        "created_at": created_at,
    }


def analyze_and_save_invoice(document_bytes: bytes) -> dict:
    validate_document_bytes(document_bytes)

    initialize_database()
    sha256 = document_hash(document_bytes)
    claim_document(sha256)
    try:
        reserve_ai_request(
            "invoice_analysis",
            "MAX_DAILY_INVOICE_ANALYSES",
            "ENABLE_INVOICE_ANALYSIS",
        )
        return _process_claimed_invoice(document_bytes, sha256)
    finally:
        release_document(sha256)
        release_business_claim(sha256)
