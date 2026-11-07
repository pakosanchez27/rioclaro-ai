"""Cuotas diarias atómicas; el día de cuota comienza a las 00:00 UTC."""

import math
import os
import time as time_module
from datetime import datetime, time, timedelta, timezone

from database.connection import get_connection
from database.table_storage import StorageConflictError


class QuotaExceededError(Exception):
    def __init__(self, resets_at: str, retry_after_seconds: int):
        super().__init__("Cuota diaria de IA agotada")
        self.resets_at = resets_at
        self.retry_after_seconds = retry_after_seconds


class AiOperationDisabledError(Exception):
    pass


OPERATIONS = {
    "assistant": ("MAX_DAILY_ASSISTANT_QUESTIONS", "ENABLE_ASSISTANT", 100),
    "invoice_analysis": ("MAX_DAILY_INVOICE_ANALYSES", "ENABLE_INVOICE_ANALYSIS", 20),
}


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _scope() -> str:
    environment = os.getenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development").strip().lower()
    return "development" if environment == "development" and not os.getenv("WEBSITE_INSTANCE_ID") else "production"


def _settings(operation: str) -> tuple[str, bool, int]:
    if operation not in OPERATIONS:
        raise ValueError("Operacion de cuota desconocida")
    legacy_limit, enabled_env, default_local = OPERATIONS[operation]
    scope = _scope()
    # El disco de Azure Functions no es un contador compartido entre instancias.
    if os.getenv("WEBSITE_INSTANCE_ID") and os.getenv("STORAGE_BACKEND", "sqlite").strip().lower() != "table":
        raise AiOperationDisabledError("Cuotas compartidas no configuradas para Azure")
    enabled = os.getenv(enabled_env, "true").strip().lower() == "true"
    specific_env = f"{'DEV' if scope == 'development' else 'PROD'}_{legacy_limit}"
    raw_limit = os.getenv(specific_env)
    if raw_limit is None and scope == "development":
        raw_limit = os.getenv(legacy_limit, str(default_local))
    if raw_limit is None:
        raise AiOperationDisabledError("Cuota de produccion no configurada")
    try:
        limit = int(raw_limit)
    except ValueError as exc:
        raise AiOperationDisabledError("Cuota de IA no configurada") from exc
    if limit < 1:
        raise AiOperationDisabledError("Cuota de IA no configurada")
    return scope, enabled, limit


def _period(now: datetime) -> tuple[str, str, int]:
    now = now.astimezone(timezone.utc)
    reset = datetime.combine(now.date() + timedelta(days=1), time.min, timezone.utc)
    return now.date().isoformat(), reset.isoformat().replace("+00:00", "Z"), max(1, math.ceil((reset - now).total_seconds()))


def _migrate_legacy(connection) -> None:
    # Preservar consumo de la clave antigua y evitar restaurarlo tras reiniciar.
    connection.execute(
        """INSERT INTO ai_usage_daily (usage_date, operation, request_count)
           SELECT usage_date, 'development:' || operation, request_count
           FROM ai_usage_daily WHERE operation IN ('assistant', 'invoice_analysis')
           ON CONFLICT (usage_date, operation) DO UPDATE SET
           request_count = MAX(request_count, excluded.request_count)"""
    )
    connection.execute(
        "DELETE FROM ai_usage_daily WHERE operation IN ('assistant', 'invoice_analysis')"
    )


def get_quota_status(operation: str) -> dict:
    scope, enabled, limit = _settings(operation)
    usage_date, resets_at, retry_after = _period(_now_utc())
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _migrate_legacy(connection)
        row = connection.execute(
            "SELECT request_count FROM ai_usage_daily WHERE usage_date = ? AND operation = ?",
            (usage_date, f"{scope}:{operation}"),
        ).fetchone()
    used = row["request_count"] if row else 0
    return {
        "remaining": max(0, limit - used) if enabled else 0,
        "limit": limit,
        "resets_at": resets_at,
        "timezone": "UTC",
        "enabled": enabled,
        "retry_after_seconds": retry_after if used >= limit else None,
    }


def reserve_ai_request(operation: str, limit_env: str, enabled_env: str) -> None:
    expected_limit, expected_enabled, _ = OPERATIONS.get(operation, (None, None, None))
    if (limit_env, enabled_env) != (expected_limit, expected_enabled):
        raise ValueError("Configuracion de cuota incorrecta")
    scope, enabled, limit = _settings(operation)
    if not enabled:
        raise AiOperationDisabledError("Operacion de IA suspendida")
    usage_date, resets_at, retry_after = _period(_now_utc())
    for attempt in range(12):
        try:
            with get_connection() as connection:
                connection.execute("BEGIN IMMEDIATE")
                _migrate_legacy(connection)
                row = connection.execute(
                    "SELECT request_count FROM ai_usage_daily WHERE usage_date = ? AND operation = ?",
                    (usage_date, f"{scope}:{operation}"),
                ).fetchone()
                if row and row["request_count"] >= limit:
                    raise QuotaExceededError(resets_at, retry_after)
                connection.execute(
                    """INSERT INTO ai_usage_daily (usage_date, operation, request_count)
                       VALUES (?, ?, 1) ON CONFLICT (usage_date, operation)
                       DO UPDATE SET request_count = request_count + 1""",
                    (usage_date, f"{scope}:{operation}"),
                )
            return
        except StorageConflictError:
            if attempt == 11:
                raise AiOperationDisabledError("Cuota temporalmente ocupada")
            time_module.sleep(0.01 * (attempt + 1))


def reset_local_quotas(operation: str | None = None) -> int:
    """Borra sólo cuotas del día local; nunca datos de negocio ni cuotas publicadas."""
    if (os.getenv("DEMO_MODE", "").strip().lower() != "true"
            or os.getenv("AZURE_FUNCTIONS_ENVIRONMENT", "").strip().lower() != "development"
            or os.getenv("WEBSITE_INSTANCE_ID")):
        raise PermissionError("Reinicio permitido solo en desarrollo local con DEMO_MODE=true")
    if operation is not None and operation not in OPERATIONS:
        raise ValueError("Operacion de cuota desconocida")
    usage_date = _now_utc().date().isoformat()
    with get_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        _migrate_legacy(connection)
        operations = (operation,) if operation else tuple(OPERATIONS)
        cursor = connection.execute(
            f"DELETE FROM ai_usage_daily WHERE usage_date = ? AND operation IN ({','.join('?' for _ in operations)})",
            (usage_date, *(f"development:{item}" for item in operations)),
        )
        return cursor.rowcount
