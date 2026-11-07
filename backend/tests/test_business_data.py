import pytest

from database.connection import get_connection
from repositories.business_data import (
    find_product, get_inventory, get_order, get_current_policy,
    get_low_stock_products, get_pending_orders,
)
from seed_business_demo import seed_business_demo_data


@pytest.fixture
def business_database(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_DB_PATH", str(tmp_path / "business.db"))
    seed_business_demo_data()


def test_seed_is_idempotent_and_has_five_branches(business_database):
    seed_business_demo_data()
    with get_connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM branches").fetchone()[0] == 5
        assert connection.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 3


@pytest.mark.parametrize("alias", ["Cloro 1L", "CLORO LITRO", "Blanqueador 1000ml"])
def test_validated_aliases_resolve_same_product(business_database, alias):
    assert find_product(alias)["sku"] == "LIM-001"


@pytest.mark.parametrize("branch", ["Guadalajara", "Zapopan", "León", "Querétaro", "Aguascalientes"])
def test_inventory_uses_same_criteria_for_all_branches(business_database, branch):
    result = get_inventory("Cloro 1L", branch)
    assert result["inventory"][0]["branch_name"] == branch
    assert result["inventory"][0]["quantity"] >= 0


def test_order_and_current_policy_are_verifiable(business_database):
    assert get_order("PED-001")["branch_name"] == "León"
    assert get_order("PED-999") is None
    assert get_current_policy("devoluciones")["version"] == 2
    assert "Versión histórica" not in get_current_policy("devoluciones")["content"]


def test_low_stock_and_pending_orders(business_database):
    assert any(row["quantity"] == 8 for row in get_low_stock_products())
    assert {row["folio"] for row in get_pending_orders()} == {"PED-001", "PED-003"}
