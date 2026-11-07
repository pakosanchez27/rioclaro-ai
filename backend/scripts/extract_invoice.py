
import json
import os
import sys
from pathlib import Path

from azure.core.exceptions import HttpResponseError

from services.document_intelligence import (
    extract_invoice,
    DocumentValidationError,
    InvoiceExtractionError,
)


def load_local_settings():
    path = Path(__file__).resolve().parents[1] / "local.settings.json"

    settings = json.loads(
        path.read_text(encoding="utf-8-sig")
    )

    values = settings.get("Values", {})

    for key in (
        "DOCUMENTINTELLIGENCE_ENDPOINT",
        "DOCUMENTINTELLIGENCE_API_KEY",
    ):
        if values.get(key):
            os.environ[key] = values[key]


def main():
    if len(sys.argv) != 2:
        print(
            "Uso: python -m scripts.extract_invoice ruta_factura.pdf"
        )
        sys.exit(1)

    path = Path(sys.argv[1])

    if not path.is_file():
        print("No se encontro el documento.")
        sys.exit(1)

    load_local_settings()

    try:
        result = extract_invoice(path.read_bytes())

        print(json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ))

    except (DocumentValidationError, InvoiceExtractionError) as exc:
        print(f"Validacion: {exc}", file=sys.stderr)
        sys.exit(1)

    except HttpResponseError as exc:
        print(
            f"Azure respondio HTTP {exc.status_code}. "
            "Revisa el recurso, las credenciales y el documento.",
            file=sys.stderr,
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
