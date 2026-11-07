import pytest

from repositories.business_data import get_branch_report, get_demo_options
from repositories.complaints import create_complaint, get_complaint, ComplaintInputError
from seed_business_demo import seed_business_demo_data


@pytest.fixture
def business_database(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "complaints.db"))
    seed_business_demo_data()


def test_complaint_has_real_folio_and_can_be_queried(business_database):
    saved = create_complaint("PED-001", "LEO", "La entrega llegó incompleta", "delivery")

    assert saved["folio"].startswith("QUE-")
    complaint = get_complaint(saved["folio"])
    assert complaint["status"] == "open"
    assert complaint["branch_name"] == "León"


def test_complaint_rejects_order_from_another_branch(business_database):
    with pytest.raises(ComplaintInputError):
        create_complaint("PED-001", "GDL", "La entrega llegó incompleta", "delivery")


def test_report_is_derived_from_orders(business_database):
    report = get_branch_report()

    assert len(report["branches"]) == 5
    by_code = {row["code"]: row for row in report["branches"]}
    assert by_code["GDL"]["delivered_sales"] == 189.0
    assert by_code["LEO"]["delivered_sales"] == 0
    assert by_code["LEO"]["pending_orders"] == 1
    assert report["products_sold"][0]["sku"] == "LIM-002"


def test_options_use_database_records(business_database):
    options = get_demo_options()
    assert len(options["branches"]) == 5
    assert {order["folio"] for order in options["orders"]} == {"PED-001", "PED-002", "PED-003"}
