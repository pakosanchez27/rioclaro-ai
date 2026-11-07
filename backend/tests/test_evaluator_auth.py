import hashlib
import json
from datetime import datetime, timedelta, timezone

import azure.functions as func
import pytest

from database.connection import initialize_database, get_connection
from function_app import auth_evaluator_login, auth_evaluator_logout, invoices_list, assistant_quota
from security import evaluator_auth


@pytest.fixture
def evaluation(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "evaluation.db"))
    monkeypatch.setenv("STORAGE_BACKEND", "sqlite")
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Production")
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    monkeypatch.setenv("DEMO_MODE", "false")
    monkeypatch.setenv("EVALUATOR_ACCESS_ENABLED", "true")
    salt = bytes.fromhex("ab" * 16)
    monkeypatch.setenv("EVALUATOR_CODE_SALT", salt.hex())
    monkeypatch.setenv("EVALUATOR_CODE_HASH", hashlib.pbkdf2_hmac("sha256", b"test-code", salt, 210_000).hex())
    initialize_database()


def request(method, route, body=b"", token=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    return func.HttpRequest(method=method, url=f"http://localhost/api/{route}", body=body, headers=headers)


def test_login_authorization_logout_and_no_plain_token_storage(evaluation):
    assert invoices_list(request("GET", "invoices")).status_code == 401
    assert assistant_quota(request("GET", "assistant/quota")).status_code == 401
    response = auth_evaluator_login(request("POST", "auth/evaluator/login", json.dumps({"code": "test-code"}).encode()))
    assert response.status_code == 200
    token = json.loads(response.get_body())["access_token"]
    assert token.startswith("ev_")
    with get_connection() as connection:
        rows = connection.execute("SELECT token_hash FROM evaluation_sessions").fetchall()
    assert len(rows) == 1 and token[3:] not in rows[0][0]
    assert invoices_list(request("GET", "invoices", token=token)).status_code == 200
    assert auth_evaluator_logout(request("POST", "auth/evaluator/logout", token=token)).status_code == 204
    assert invoices_list(request("GET", "invoices", token=token)).status_code == 401


def test_wrong_code_lockout_and_expiration(evaluation, monkeypatch):
    bad = json.dumps({"code": "wrong"}).encode()
    for _ in range(8):
        assert auth_evaluator_login(request("POST", "auth/evaluator/login", bad)).status_code == 401
    assert auth_evaluator_login(request("POST", "auth/evaluator/login", bad)).status_code == 429
    monkeypatch.setattr(evaluator_auth, "_now", lambda: datetime.now(timezone.utc) + timedelta(minutes=16))
    good = auth_evaluator_login(request("POST", "auth/evaluator/login", json.dumps({"code": "test-code"}).encode()))
    assert good.status_code == 200
    token = json.loads(good.get_body())["access_token"]
    monkeypatch.setattr(evaluator_auth, "_now", lambda: datetime.now(timezone.utc) + timedelta(hours=3))
    assert invoices_list(request("GET", "invoices", token=token)).status_code == 401


def test_access_switch_revokes_sessions(evaluation, monkeypatch):
    token, _ = evaluator_auth.login("test-code")
    monkeypatch.setenv("EVALUATOR_ACCESS_ENABLED", "false")
    assert invoices_list(request("GET", "invoices", token=f"ev_{token}")).status_code == 401
    with pytest.raises(evaluator_auth.EvaluatorAuthError):
        evaluator_auth.login("test-code")
