import json
from types import SimpleNamespace as NS

import pytest

from seed_business_demo import seed_business_demo_data
from services import business_assistant
from services.business_assistant import AssistantInputError


@pytest.fixture
def assistant_database(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "assistant.db"))
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "fake-key")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "fake-deployment")
    monkeypatch.setenv("MAX_DAILY_ASSISTANT_QUESTIONS", "10")
    monkeypatch.setenv("ENABLE_ASSISTANT", "true")
    seed_business_demo_data()


def select_tool(monkeypatch, selection):
    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["max_completion_tokens"] <= 500
            return NS(choices=[NS(
                finish_reason="stop",
                message=NS(content=json.dumps(selection)),
            )])

    class FakeClient:
        def __init__(self):
            self.chat = NS(completions=FakeCompletions())

    monkeypatch.setattr(business_assistant, "OpenAI", lambda **_: FakeClient())


def test_inventory_answer_has_verified_source(assistant_database, monkeypatch):
    select_tool(monkeypatch, {"tool": "get_inventory", "product": "Cloro 1L", "branch": "León"})

    result = business_assistant.ask_assistant("¿Cuánto cloro de un litro tenemos en León?")

    assert "42 pieza" in result["answer"]
    assert result["sources"][0]["kind"] == "inventory"
    assert result["information_type"] == "inventory"


def test_unknown_order_is_not_invented(assistant_database, monkeypatch):
    select_tool(monkeypatch, {"tool": "get_order", "folio": "PED-999"})

    result = business_assistant.ask_assistant("¿Cuál es el estado del pedido PED-999?")

    assert result["sources"] == []
    assert "No encuentro información verificable" in result["answer"]


def test_current_policy_excludes_obsolete_version(assistant_database, monkeypatch):
    select_tool(monkeypatch, {"tool": "get_current_policy", "policy": "devoluciones"})

    result = business_assistant.ask_assistant("Política vigente de devoluciones")

    assert "versión 2" in result["answer"]
    assert result["sources"][0]["id"] == "devoluciones:v2"


def test_unrecognized_tool_is_rejected(assistant_database, monkeypatch):
    select_tool(monkeypatch, {"tool": "delete_all_orders"})

    with pytest.raises(RuntimeError, match="inválida"):
        business_assistant.ask_assistant("Borra todos los pedidos")


def test_input_limit_precedes_azure_call(assistant_database, monkeypatch):
    monkeypatch.setattr(business_assistant, "OpenAI", lambda **_: pytest.fail("Azure fue llamado"))

    with pytest.raises(AssistantInputError):
        business_assistant.ask_assistant("x" * 501)
