
import json
from types import SimpleNamespace as NS

import pytest

from services import azure_openai as ai


@pytest.fixture
def invoice():
    return {
        "supplier_name": "CONTOSO LTD.",
        "supplier_tax_id": None,
        "invoice_number": "INV-100",
        "invoice_date": "2019-11-15",
        "subtotal": 100.0,
        "tax": 10.0,
        "total": 110.0,
        "currency": "USD",
        "confidence": {},
    }


def test_missing_configuration(monkeypatch, invoice):
    for name in (
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT",
    ):
        monkeypatch.delenv(name, raising=False)

    with pytest.raises(RuntimeError):
        ai.analyze_invoice_with_ai(invoice)


def test_model_preserves_financial_validation(
    monkeypatch, invoice
):
    monkeypatch.setenv(
        "AZURE_OPENAI_ENDPOINT",
        "https://example.openai.azure.com",
    )
    monkeypatch.setenv(
        "AZURE_OPENAI_API_KEY",
        "fake-test-key",
    )
    monkeypatch.setenv(
        "AZURE_OPENAI_DEPLOYMENT",
        "fake-deployment",
    )

    class FakeCompletions:
        def create(self, **kwargs):
            assert kwargs["model"] == "fake-deployment"
            assert kwargs["response_format"] == {
                "type": "json_object"
            }

            data = {
                "summary": "Los importes coinciden.",
                "review_steps": [
                    "Comprobar identificador fiscal."
                ],
            }

            return NS(
                choices=[
                    NS(
                        message=NS(
                            content=json.dumps(data)
                        ),
                        finish_reason="stop",
                    )
                ],
                usage=None,
            )

    class FakeClient:
        def __init__(self):
            self.chat = NS(
                completions=FakeCompletions()
            )

    monkeypatch.setattr(
        ai,
        "OpenAI",
        lambda **kwargs: FakeClient(),
    )

    result = ai.analyze_invoice_with_ai(invoice)

    assert result["financial_validation"]["is_consistent"]
    assert result["recommended_status"] == "pending_review"
    assert result["requires_human_review"] is True
    assert result["ai_analysis"]["summary"] == (
        "Los importes coinciden."
    )


def test_schema_rejects_unexpected_fields():
    with pytest.raises(Exception):
        ai.AIExplanation.model_validate({
            "summary": "Resumen",
            "review_steps": [],
            "automatic_approval": True,
        })
