import json

import azure.functions as func

from database.connection import initialize_database
from function_app import assistant_ask, assistant_quota
from services.ai_quota import reserve_ai_request


def _request(method, route, body=b""):
    return func.HttpRequest(
        method=method, url=f"http://localhost/api/{route}", body=body,
        headers={"Content-Type": "application/json"},
    )


def test_quota_endpoint_and_429(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "isolated.db"))
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    monkeypatch.setenv("DEV_MAX_DAILY_ASSISTANT_QUESTIONS", "1")
    initialize_database()
    reserve_ai_request("assistant", "MAX_DAILY_ASSISTANT_QUESTIONS", "ENABLE_ASSISTANT")

    response = assistant_quota(_request("GET", "assistant/quota"))
    assert response.status_code == 200
    payload = json.loads(response.get_body())
    assert payload["remaining"] == 0
    assert payload["timezone"] == "UTC"
    assert "SQLITE_DB_PATH" not in payload

    def exhausted(*args):
        reserve_ai_request("assistant", "MAX_DAILY_ASSISTANT_QUESTIONS", "ENABLE_ASSISTANT")
    monkeypatch.setattr("function_app.ask_assistant", exhausted)
    response = assistant_ask(_request(
        "POST", "assistant/ask", json.dumps({"message": "Hola"}).encode()
    ))
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
    assert json.loads(response.get_body())["resets_at"] == payload["resets_at"]
