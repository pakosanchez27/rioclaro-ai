"""Temporary evaluator access. Only SHA-256 token digests are persisted."""

import hashlib
import hmac
import os
import secrets
import time
from datetime import datetime, timedelta, timezone

from database.connection import get_connection
from database.table_storage import StorageConflictError

SESSION_HOURS = 2
MAX_FAILURES = 8
LOCK_MINUTES = 15


class EvaluatorAuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.status_code = status_code


def enabled() -> bool:
    return os.getenv("EVALUATOR_ACCESS_ENABLED", "false").lower() == "true"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _configured_hash() -> bytes:
    salt = os.getenv("EVALUATOR_CODE_SALT", "")
    digest = os.getenv("EVALUATOR_CODE_HASH", "")
    if len(salt) < 32 or len(digest) != 64:
        raise EvaluatorAuthError("Acceso de evaluacion no configurado", 503)
    try:
        bytes.fromhex(salt)
        return bytes.fromhex(digest)
    except ValueError as exc:
        raise EvaluatorAuthError("Acceso de evaluacion no configurado", 503) from exc


def _valid_code(code: str) -> bool:
    expected = _configured_hash()
    if not isinstance(code, str) or len(code) > 256:
        return False
    actual = hashlib.pbkdf2_hmac("sha256", code.encode(), bytes.fromhex(os.environ["EVALUATOR_CODE_SALT"]), 210_000)
    return hmac.compare_digest(actual, expected)


def _retry(operation):
    for attempt in range(12):
        try:
            return operation()
        except StorageConflictError:
            if attempt == 11:
                raise EvaluatorAuthError("Acceso temporalmente ocupado", 503)
            time.sleep(0.01 * (attempt + 1))


def login(code: str) -> tuple[str, str]:
    if not enabled():
        raise EvaluatorAuthError("Acceso de evaluacion suspendido", 503)
    valid = _valid_code(code)

    def attempt():
        now = _now()
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT failed_count, locked_until FROM evaluation_login_guard WHERE id = 'global'").fetchone()
            if row and row["failed_count"] >= MAX_FAILURES and row["locked_until"] > _iso(now):
                raise EvaluatorAuthError("Demasiados intentos. Intenta más tarde.", 429)
            if not valid:
                count = (row["failed_count"] if row and row["locked_until"] > _iso(now) else 0) + 1
                until = _iso(now + timedelta(minutes=LOCK_MINUTES))
                connection.execute("INSERT INTO evaluation_login_guard VALUES ('global', ?, ?) ON CONFLICT(id) DO UPDATE SET failed_count = excluded.failed_count, locked_until = excluded.locked_until", (count, until))
                return None
            token = secrets.token_urlsafe(32)
            expires = _iso(now + timedelta(hours=SESSION_HOURS))
            connection.execute("INSERT INTO evaluation_sessions VALUES (?, ?)", (hashlib.sha256(token.encode()).hexdigest(), expires))
            connection.execute("DELETE FROM evaluation_sessions WHERE expires_at <= ?", (_iso(now),))
            return token, expires

    result = _retry(attempt)
    if result is None:
        raise EvaluatorAuthError("Credencial incorrecta")
    return result


def validate_session(token: str) -> dict:
    if not enabled() or not isinstance(token, str) or len(token) > 256:
        raise EvaluatorAuthError("Sesion expirada")
    digest = hashlib.sha256(token.encode()).hexdigest()
    with get_connection() as connection:
        row = connection.execute("SELECT expires_at FROM evaluation_sessions WHERE token_hash = ?", (digest,)).fetchone()
    if not row or row["expires_at"] <= _iso(_now()):
        raise EvaluatorAuthError("Sesion expirada")
    return {"user_id": "evaluator", "tenant_id": "evaluation", "username": "Evaluador", "roles": ["analyst"]}


def logout(token: str) -> None:
    if not token or len(token) > 256:
        return
    digest = hashlib.sha256(token.encode()).hexdigest()
    _retry(lambda: _delete_session(digest))


def _delete_session(digest: str) -> None:
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("DELETE FROM evaluation_sessions WHERE token_hash = ?", (digest,))
