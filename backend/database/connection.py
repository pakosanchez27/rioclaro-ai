import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "rioclaro.db"


def get_database_path() -> Path:
    return Path(os.getenv("SQLITE_DB_PATH", str(DEFAULT_DB_PATH)))


def storage_backend() -> str:
    backend = os.getenv("STORAGE_BACKEND", "sqlite").strip().lower()
    if backend not in ("sqlite", "table"):
        raise RuntimeError("STORAGE_BACKEND debe ser sqlite o table")
    if os.getenv("WEBSITE_INSTANCE_ID") and backend == "sqlite":
        raise RuntimeError("SQLite local no es persistente en Azure Functions")
    return backend


@contextmanager
def get_connection():
    if storage_backend() == "table":
        from database.table_storage import get_table_connection
        with get_table_connection() as connection:
            yield connection
        return
    path = get_database_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database():
    if storage_backend() == "table":
        from database.table_storage import get_table_client
        get_table_client()
        return
    schema_path = Path(__file__).with_name("schema.sql")

    with get_connection() as connection:
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )
