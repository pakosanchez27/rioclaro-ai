"""Azure Tables adapter for the small demo dataset.

All rows share one partition so SQLite transactions can be committed as
Azure entity group transactions. The in-memory SQL copy is never persistent.
"""

import base64
import json
import os
import sqlite3
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from azure.core import MatchConditions
from azure.core.exceptions import HttpResponseError
from azure.data.tables import TableServiceClient
from azure.identity import DefaultAzureCredential

SCHEMA = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
PARTITION = "demo"
MAX_ROWS = 1000
MAX_TRANSACTION_OPERATIONS = 100
MAX_PAYLOAD_UTF16_BYTES = 60 * 1024


class StorageConflictError(RuntimeError):
    """A conditional write lost a race against another request."""


class StorageCapacityError(RuntimeError):
    """The demo dataset exceeded the adapter's documented bounds."""


@lru_cache(maxsize=4)
def _client(endpoint: str, table_name: str):
    service = TableServiceClient(endpoint=endpoint, credential=DefaultAzureCredential())
    return service.create_table_if_not_exists(table_name=table_name)


def get_table_client():
    endpoint = os.getenv("AZURE_TABLE_ACCOUNT_URL", "").strip()
    table_name = os.getenv("AZURE_TABLE_NAME", "RioClaroDemo").strip()
    if not endpoint.startswith("https://") or not table_name:
        raise RuntimeError("Azure Table Storage no esta configurado")
    return _client(endpoint, table_name)


def _schema_columns(connection):
    tables = {}
    for row in connection.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ):
        name = row["name"]
        info = connection.execute(f"PRAGMA table_info({name})").fetchall()
        columns = [item["name"] for item in info]
        keys = [item["name"] for item in sorted(info, key=lambda item: item["pk"]) if item["pk"]]
        tables[name] = (columns, keys)
    return tables


def _row_key(name: str, row: dict, keys: list[str]) -> str:
    encoded = base64.urlsafe_b64encode(
        json.dumps([row[key] for key in keys], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    return f"{name}|{encoded}"


def _payload(row: dict) -> str:
    value = json.dumps(row, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))
    if len(value.encode("utf-16-le")) > MAX_PAYLOAD_UTF16_BYTES:
        raise StorageCapacityError("Una entidad supera el tamano admitido por Azure Tables")
    return value


def _etag(entity) -> str | None:
    metadata = getattr(entity, "metadata", None) or {}
    return metadata.get("etag") or entity.get("etag")


def _snapshot(connection, tables):
    result = {}
    for name, (columns, keys) in tables.items():
        for record in connection.execute(f"SELECT * FROM {name}"):
            row = {column: record[column] for column in columns}
            result[_row_key(name, row, keys)] = (name, _payload(row))
            if len(result) > MAX_ROWS:
                raise StorageCapacityError("La demo supera el limite de 1000 filas")
    return result


@contextmanager
def get_table_connection():
    client = get_table_client()
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    try:
        connection.executescript(SCHEMA)
        tables = _schema_columns(connection)
        original_entities = {}
        for entity in client.query_entities(query_filter="PartitionKey eq 'demo'"):
            row_key = entity["RowKey"]
            name = entity["EntityType"]
            if name not in tables:
                raise StorageCapacityError("Tipo de entidad desconocido en Azure Tables")
            row = json.loads(entity["Payload"])
            columns = tables[name][0]
            connection.execute(
                f"INSERT INTO {name} ({','.join(columns)}) VALUES ({','.join('?' for _ in columns)})",
                tuple(row.get(column) for column in columns),
            )
            original_entities[row_key] = (name, entity["Payload"], _etag(entity))
            if len(original_entities) > MAX_ROWS:
                raise StorageCapacityError("La demo supera el limite de 1000 filas")
        connection.commit()
        try:
            yield connection
            current = _snapshot(connection, tables)
            operations = []
            for row_key, (name, payload) in current.items():
                old = original_entities.get(row_key)
                if old and old[1] == payload:
                    continue
                entity = {"PartitionKey": PARTITION, "RowKey": row_key,
                          "EntityType": name, "Payload": payload}
                if old:
                    if not old[2]:
                        raise StorageCapacityError("Falta ETag para escritura condicional")
                    operations.append(("update", entity, {"mode": "replace", "etag": old[2],
                                                         "match_condition": MatchConditions.IfNotModified}))
                else:
                    operations.append(("create", entity))
            for row_key, (_, _, etag) in original_entities.items():
                if row_key not in current:
                    if not etag:
                        raise StorageCapacityError("Falta ETag para borrado condicional")
                    operations.append(("delete", {"PartitionKey": PARTITION, "RowKey": row_key},
                                       {"etag": etag, "match_condition": MatchConditions.IfNotModified}))
            if operations:
                if len(operations) > MAX_TRANSACTION_OPERATIONS:
                    raise StorageCapacityError("Transaccion supera 100 operaciones de Azure Tables")
                try:
                    client.submit_transaction(operations)
                except HttpResponseError as exc:
                    if exc.status_code in (409, 412):
                        raise StorageConflictError("Conflicto de escritura concurrente") from exc
                    raise
        except Exception:
            connection.rollback()
            raise
    finally:
        connection.close()
