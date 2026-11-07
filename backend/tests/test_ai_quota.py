from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest

from database.connection import get_connection, initialize_database
from services.ai_quota import (
    reserve_ai_request,
    QuotaExceededError,
    AiOperationDisabledError,
    get_quota_status,
    reset_local_quotas,
)
from services import ai_quota


@pytest.fixture
def quota_database(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "quota.db"))
    monkeypatch.setenv("DEV_MAX_DAILY_INVOICE_ANALYSES", "2")
    monkeypatch.setenv("ENABLE_INVOICE_ANALYSIS", "true")
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    initialize_database()


def reserve():
    reserve_ai_request(
        "invoice_analysis",
        "MAX_DAILY_INVOICE_ANALYSES",
        "ENABLE_INVOICE_ANALYSIS",
    )


def test_daily_limit_is_enforced(quota_database):
    reserve()
    reserve()

    with pytest.raises(QuotaExceededError):
        reserve()


def test_concurrent_requests_cannot_exceed_limit(quota_database):
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(reserve) for _ in range(6)]

    successes = sum(future.exception() is None for future in futures)
    assert successes == 2
    assert all(
        future.exception() is None or isinstance(future.exception(), QuotaExceededError)
        for future in futures
    )

    with get_connection() as connection:
        count = connection.execute(
            "SELECT request_count FROM ai_usage_daily WHERE operation = 'development:invoice_analysis'"
        ).fetchone()[0]
    assert count == 2


def test_switch_disables_costly_operation(quota_database, monkeypatch):
    monkeypatch.setenv("ENABLE_INVOICE_ANALYSIS", "false")

    with pytest.raises(AiOperationDisabledError):
        reserve()


def test_status_reset_and_business_data_survives(quota_database, monkeypatch):
    with get_connection() as connection:
        connection.execute("INSERT INTO ai_usage_daily VALUES ('2026-11-07', 'assistant', 3)")
        connection.execute(
            "INSERT INTO branches (id, code, name, city, state, status) VALUES ('b1', 'GDL', 'Guadalajara', 'Guadalajara', 'Jalisco', 'active')"
        )
    monkeypatch.setattr(ai_quota, "_now_utc", lambda: datetime(2026, 11, 7, 12, tzinfo=timezone.utc))
    status = get_quota_status("assistant")
    assert status["remaining"] == 97
    assert status["resets_at"] == "2026-11-08T00:00:00Z"
    assert status["timezone"] == "UTC"
    assert reset_local_quotas("assistant") == 1
    assert get_quota_status("assistant")["remaining"] == 100
    with get_connection() as connection:
        assert connection.execute("SELECT count(*) FROM branches").fetchone()[0] == 1


def test_next_day_resets_automatically(quota_database, monkeypatch):
    monkeypatch.setattr(ai_quota, "_now_utc", lambda: datetime(2026, 11, 7, 23, 59, tzinfo=timezone.utc))
    reserve()
    reserve()
    with pytest.raises(QuotaExceededError) as error:
        reserve()
    assert error.value.retry_after_seconds == 60
    monkeypatch.setattr(ai_quota, "_now_utc", lambda: datetime(2026, 11, 8, 0, 0, tzinfo=timezone.utc))
    assert get_quota_status("invoice_analysis")["remaining"] == 2


def test_reset_forbidden_outside_local_demo(quota_database, monkeypatch):
    reserve()
    monkeypatch.setenv("WEBSITE_INSTANCE_ID", "deployed")
    with pytest.raises(PermissionError):
        reset_local_quotas()
    with pytest.raises(AiOperationDisabledError):
        reserve()


def test_production_limit_is_independent(quota_database, monkeypatch):
    reserve()
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Production")
    with pytest.raises(AiOperationDisabledError):
        reserve()
    monkeypatch.setenv("PROD_MAX_DAILY_INVOICE_ANALYSES", "1")
    reserve()
    with pytest.raises(QuotaExceededError):
        reserve()
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
    assert get_quota_status("invoice_analysis")["remaining"] == 1
