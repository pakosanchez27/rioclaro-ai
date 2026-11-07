"""Copy a small local SQLite snapshot to Azure Tables without overwriting rows.

Requires STORAGE_BACKEND=table, AZURE_TABLE_ACCOUNT_URL and Azure credentials.
This script writes to Azure only when --confirm-azure-write is supplied.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from database.table_storage import (  # noqa: E402
    PARTITION, MAX_ROWS, MAX_TRANSACTION_OPERATIONS, _payload, _row_key,
    _schema_columns, get_table_client,
)


def migrate(source: Path, client) -> tuple[int, int]:
    if not source.is_file():
        raise ValueError("La base SQLite de origen no existe")
    original = sqlite3.connect(f"file:{source.resolve().as_posix()}?mode=ro", uri=True)
    snapshot = sqlite3.connect(":memory:")
    snapshot.row_factory = sqlite3.Row
    try:
        original.backup(snapshot)
        tables = _schema_columns(snapshot)
        local = {}
        for name, (columns, keys) in tables.items():
            for record in snapshot.execute(f"SELECT * FROM {name}"):
                row = {column: record[column] for column in columns}
                key = _row_key(name, row, keys)
                local[key] = {"PartitionKey": PARTITION, "RowKey": key,
                              "EntityType": name, "Payload": _payload(row)}
                if len(local) > MAX_ROWS:
                    raise ValueError("Más de 1000 filas: requiere migración por lotes diseñada aparte")
        remote = {entity["RowKey"]: entity for entity in
                  client.query_entities(query_filter="PartitionKey eq 'demo'")}
        for key, entity in local.items():
            existing = remote.get(key)
            if existing and existing["Payload"] != entity["Payload"]:
                raise ValueError(f"Conflicto remoto en {entity['EntityType']}; no se sobrescribió")
        missing = [entity for key, entity in local.items() if key not in remote]
        if len(missing) > MAX_TRANSACTION_OPERATIONS:
            raise ValueError("Más de 100 filas nuevas: se requiere migración por lotes diseñada aparte")
        if missing:
            client.submit_transaction([("create", entity) for entity in missing])
        return len(missing), len(local) - len(missing)
    finally:
        snapshot.close()
        original.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--confirm-azure-write", action="store_true", required=True)
    args = parser.parse_args()
    import os
    if os.getenv("STORAGE_BACKEND") != "table":
        parser.error("STORAGE_BACKEND=table es obligatorio")
    created, existing = migrate(args.source, get_table_client())
    print(f"Filas creadas: {created}; ya idénticas: {existing}. No se sobrescribieron datos remotos.")


if __name__ == "__main__":
    main()
