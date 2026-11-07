import json

import azure.functions as func
import pytest

from function_app import invoices_detail, business_reports, complaints_create
from seed_demo import seed_demo_data
from seed_business_demo import seed_business_demo_data


@pytest.fixture
def local_database(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "routes.db"))
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    seed_demo_data()
    seed_business_demo_data()


def request(method, route, body=b"", route_params=None):
    return func.HttpRequest(
        method=method,
        url=f"http://localhost/api/{route}",
        body=body,
        route_params=route_params or {},
        headers={"Content-Type": "application/json"},
    )


def test_stats_path_returns_stats_even_when_host_uses_detail_route(local_database):
    response = invoices_detail(request("GET", "invoices/stats", route_params={"factura_id": "stats"}))

    assert response.status_code == 200
    assert json.loads(response.get_body())["total_invoices"] == 4


def test_report_endpoint_returns_five_branches(local_database):
    response = business_reports(request("GET", "business/reports"))

    assert response.status_code == 200
    assert len(json.loads(response.get_body())["branches"]) == 5


def test_complaint_endpoint_validates_branch_and_order(local_database):
    body = json.dumps({
        "order_folio": "PED-001",
        "branch_code": "GDL",
        "category": "delivery",
        "message": "Entrega incompleta de prueba",
    }).encode()

    response = complaints_create(request("POST", "complaints", body=body))

    assert response.status_code == 400
