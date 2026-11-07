import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager


DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "data" / "rioclaro.db"


def get_database_path() -> Path:
    return Path(os.getenv("SQLITE_DB_PATH", str(DEFAULT_DB_PATH)))


@contextmanager
def get_connection():
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
    schema_path = Path(__file__).with_name("schema.sql")

    with get_connection() as connection:
        connection.executescript(
            schema_path.read_text(encoding="utf-8")
        )