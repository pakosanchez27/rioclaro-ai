
import pytest

from database.connection import (
    get_connection,
    initialize_database,
)
from repositories.invoices import (
    list_invoices,
    get_invoice,
    get_invoice_stats,
)
from seed_demo import seed_demo_data


@pytest.fixture
def demo_database(tmp_path, monkeypatch):
    database_path = tmp_path / "test_invoices.db"
    monkeypatch.setenv("SQLITE_DB_PATH", str(database_path))

    seed_demo_data()

    yield database_path


def test_database_created(demo_database):
    assert demo_database.exists()


def test_list_invoices(demo_database):
    invoices = list_invoices()
    assert len(invoices) == 4


def test_get_invoice(demo_database):
    invoice = get_invoice("factura-001")

    assert invoice is not None
    assert invoice["status"] == "validated"
    assert invoice["total"] == 1160.00


def test_invoice_not_found(demo_database):
    invoice = get_invoice("inexistente")
    assert invoice is None


def test_invoice_stats(demo_database):
    stats = get_invoice_stats()

    assert stats["total_invoices"] == 4
    assert stats["total_amount"] == pytest.approx(6281.80)
    assert stats["validated"] == 2
    assert stats["pending_review"] == 2


def test_pagination(demo_database):
    invoices = list_invoices(limit=2, offset=0)

    assert len(invoices) == 2
    assert invoices[0]["id"] == "factura-004"


def test_seed_is_idempotent(demo_database):
    seed_demo_data()
    assert len(list_invoices()) == 4
