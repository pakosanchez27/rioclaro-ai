"""Reinicia únicamente contadores de IA del día en desarrollo local.

Desde backend: python scripts/reset_local_quotas.py --confirm-local-reset
"""

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from database.connection import get_database_path, initialize_database  # noqa: E402
from services.ai_quota import reset_local_quotas  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-local-reset", action="store_true", required=True)
    parser.add_argument("--operation", choices=("assistant", "invoice_analysis", "all"), default="all")
    args = parser.parse_args()

    settings_path = BACKEND / "local.settings.json"
    if not settings_path.is_file():
        parser.error("No existe backend/local.settings.json")
    values = json.loads(settings_path.read_text(encoding="utf-8-sig")).get("Values", {})
    for key in ("DEMO_MODE", "AZURE_FUNCTIONS_ENVIRONMENT", "SQLITE_DB_PATH"):
        if key in values:
            os.environ[key] = str(values[key])
    os.chdir(BACKEND)
    if os.getenv("WEBSITE_INSTANCE_ID"):
        parser.error("Reinicio prohibido dentro de Azure Functions")

    path = get_database_path().resolve()
    if not path.is_relative_to(BACKEND.resolve()):
        parser.error("La base SQLite debe estar dentro del directorio backend")
    if not path.is_file():
        parser.error("La base SQLite local no existe")
    initialize_database()
    deleted = reset_local_quotas(None if args.operation == "all" else args.operation)
    print(f"Contadores locales reiniciados: {deleted}. Facturas y datos empresariales conservados.")


if __name__ == "__main__":
    main()
