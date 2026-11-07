
import json
import os
from pathlib import Path

from services.azure_openai import analyze_invoice_with_ai


def load_settings():
    path = (
        Path(__file__).resolve().parents[1]
        / "local.settings.json"
    )

    settings = json.loads(
        path.read_text(encoding="utf-8-sig")
    )

    values = settings.get("Values", {})

    for name in (
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
    ):
        if values.get(name):
            os.environ[name] = values[name]


def main():
    load_settings()

    # Datos extraidos anteriormente de la
    # factura de ejemplo CONTOSO.
    invoice = {
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

    result = analyze_invoice_with_ai(invoice)

    print(json.dumps(
        result,
        ensure_ascii=False,
        indent=2,
    ))


if __name__ == "__main__":
    main()
