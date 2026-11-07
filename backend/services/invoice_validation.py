
from decimal import Decimal, InvalidOperation


def to_decimal(value):
    if value is None or isinstance(value, bool):
        return None

    try:
        number = Decimal(str(value))
        return number if number.is_finite() else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def validate_invoice_data(invoice: dict) -> dict:
    if not isinstance(invoice, dict):
        raise ValueError("Se esperaba un objeto de factura")

    findings = []

    required_fields = {
        "supplier_name": "Nombre del proveedor",
        "invoice_number": "Número de factura",
        "invoice_date": "Fecha de emisión",
        "total": "Importe total",
    }

    for field, label in required_fields.items():
        value = invoice.get(field)

        if value is None or (
            isinstance(value, str) and not value.strip()
        ):
            findings.append({
                "type": "missing_field",
                "severity": "medium",
                "field": field,
                "message": f"No se identificó: {label}.",
            })

    if not invoice.get("supplier_tax_id"):
        findings.append({
            "type": "missing_field",
            "severity": "info",
            "field": "supplier_tax_id",
            "message": (
                "No se identificó el registro fiscal "
                "del proveedor."
            ),
        })

    subtotal = to_decimal(invoice.get("subtotal"))
    tax = to_decimal(invoice.get("tax"))
    total = to_decimal(invoice.get("total"))

    consistent = None
    difference = None

    if all(value is not None for value in (subtotal, tax, total)):
        expected_total = subtotal + tax
        difference = abs(expected_total - total)
        consistent = difference <= Decimal("0.01")

        if not consistent:
            findings.append({
                "type": "financial_mismatch",
                "severity": "high",
                "field": "total",
                "message": (
                    "El subtotal más los impuestos "
                    "no coincide con el total."
                ),
            })
    else:
        findings.append({
            "type": "incomplete_validation",
            "severity": "medium",
            "field": "financial_validation",
            "message": (
                "No hay suficientes importes para "
                "verificar el cálculo de la factura."
            ),
        })

    for field in ("subtotal", "tax", "total"):
        value = invoice.get(field)
        if value is not None and to_decimal(value) is None:
            findings.append({
                "type": "invalid_amount",
                "severity": "high",
                "field": field,
                "message": f"Importe inválido: {field}.",
            })

    for name, confidence in invoice.get("confidence", {}).items():
        if (
            isinstance(confidence, (int, float))
            and not isinstance(confidence, bool)
            and 0 <= confidence < 0.80
        ):
            findings.append({
                "type": "low_confidence",
                "severity": "medium",
                "field": name,
                "message": (
                    "El dato fue extraído con "
                    "baja confianza."
                ),
            })

    return {
        "invoice_number": invoice.get("invoice_number"),
        "financial_validation": {
            "subtotal": invoice.get("subtotal"),
            "tax": invoice.get("tax"),
            "total": invoice.get("total"),
            "currency": invoice.get("currency"),
            "is_consistent": consistent,
            "difference": (
                str(difference)
                if difference is not None
                else None
            ),
        },
        "findings": findings,
        "requires_human_review": bool(findings),
        "recommended_status": "pending_review",
    }
