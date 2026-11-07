import json

import azure.functions as func
import pytest

from database.connection import get_connection
from repositories.invoice_analyses import get_saved_invoice_analysis
from seed_demo import seed_demo_data
from function_app import invoices_saved_analysis, invoices_review


@pytest.fixture
def demo_database(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "analyses_test.db"))
    seed_demo_data()


def save_analysis(invoice_id="factura-003"):
    extraction = {
        "supplier_name": "Proveedor Demo",
        "invoice_number": "DEMO-003",
        "total": 2320.0,
    }
    analysis = {
        "findings": [],
        "ai_analysis": {
            "summary": "Importes revisados.",
            "review_steps": [],
        },
    }

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO invoice_analyses (
                invoice_id,
                extraction_json,
                analysis_json,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                invoice_id,
                json.dumps(extraction),
                json.dumps(analysis),
                "2026-11-07T12:00:00Z",
            ),
        )


def test_invoice_without_analysis(demo_database):
    result = get_saved_invoice_analysis("factura-001")

    assert result is None


def test_saved_analysis(demo_database):
    save_analysis()

    result = get_saved_invoice_analysis("factura-003")

    assert result is not None
    assert result["invoice_id"] == "factura-003"
    assert result["extraction"]["total"] == 2320.0
    assert result["analysis"]["ai_analysis"]["summary"] == (
        "Importes revisados."
    )


def test_analysis_query_is_parameterized(demo_database):
    save_analysis()

    result = get_saved_invoice_analysis("factura-003' OR 1=1 --")

    assert result is None


@pytest.fixture
def local_demo(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)


def analysis_request(invoice_id):
    return func.HttpRequest(
        method="GET",
        url=f"http://localhost/api/invoices/{invoice_id}/analysis",
        body=b"",
        route_params={"factura_id": invoice_id},
    )


def test_endpoint_returns_saved_analysis(demo_database, local_demo):
    save_analysis()

    response = invoices_saved_analysis(analysis_request("factura-003"))

    assert response.status_code == 200
    body = json.loads(response.get_body())
    assert body["data"]["analysis"]["ai_analysis"]["summary"] == (
        "Importes revisados."
    )


def test_endpoint_returns_null_for_seed_invoice(demo_database, local_demo):
    response = invoices_saved_analysis(analysis_request("factura-001"))

    assert response.status_code == 200
    assert json.loads(response.get_body())["data"] is None


def test_endpoint_returns_404_for_unknown_invoice(demo_database, local_demo):
    response = invoices_saved_analysis(analysis_request("missing"))

    assert response.status_code == 404


def test_endpoint_requires_authorization(demo_database, monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "false")

    response = invoices_saved_analysis(analysis_request("factura-003"))

    assert response.status_code == 401


def test_existing_review_endpoint_records_demo_decision(demo_database, local_demo):
    request = func.HttpRequest(
        method="POST",
        url="http://localhost/api/invoices/review",
        headers={"Content-Type": "application/json"},
        body=json.dumps({
            "invoice_id": "factura-003",
            "decision": "approve",
            "notes": "Comprobada",
        }).encode(),
    )

    response = invoices_review(request)

    assert response.status_code == 200
    body = json.loads(response.get_body())
    assert body["status"] == "validated"
    assert body["reviewed_by"] == "local-demo-analyst"
