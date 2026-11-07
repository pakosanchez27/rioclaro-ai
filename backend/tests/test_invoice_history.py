
import pytest

from database.connection import get_connection
from seed_demo import seed_demo_data
from services.invoice_review import review_invoice
from repositories.invoice_reviews import list_invoice_reviews


USER_ID = "usuario-test-001"


@pytest.fixture
def demo_database(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "SQLITE_DB_PATH",
        str(tmp_path / "history_test.db"),
    )
    seed_demo_data()


def test_empty_history(demo_database):
    history = list_invoice_reviews("factura-001")

    assert history["total"] == 0
    assert history["data"] == []


def test_approved_invoice_history(demo_database):
    review_invoice(
        "factura-003",
        "approve",
        USER_ID,
        "Factura verificada",
    )

    history = list_invoice_reviews("factura-003")

    assert history["total"] == 1
    assert history["data"][0]["decision"] == "approve"
    assert history["data"][0]["new_status"] == "validated"
    assert history["data"][0]["reviewed_by_oid"] == USER_ID
    assert history["data"][0]["reviewed_at"]


def test_rejected_invoice_history(demo_database):
    review_invoice(
        "factura-004",
        "reject",
        USER_ID,
        "Importe incorrecto",
    )

    history = list_invoice_reviews("factura-004")

    assert history["total"] == 1
    assert history["data"][0]["decision"] == "reject"
    assert history["data"][0]["notes"] == "Importe incorrecto"


def test_history_isolated_by_invoice(demo_database):
    review_invoice(
        "factura-003",
        "approve",
        USER_ID,
    )

    review_invoice(
        "factura-004",
        "reject",
        USER_ID,
        "Datos incorrectos",
    )

    history = list_invoice_reviews("factura-003")

    assert history["total"] == 1
    assert all(
        row["invoice_id"] == "factura-003"
        for row in history["data"]
    )


def test_history_pagination(demo_database):
    # Registros sinteticos para comprobar la paginacion
    # de futuros historiales con multiples eventos.
    with get_connection() as connection:
        for index in range(3):
            connection.execute(
                """
                INSERT INTO invoice_reviews (
                    invoice_id,
                    decision,
                    previous_status,
                    new_status,
                    notes,
                    reviewed_by_oid,
                    reviewed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "factura-003",
                    "approve",
                    "pending_review",
                    "validated",
                    f"Evento {index}",
                    USER_ID,
                    f"2026-11-0{index + 1}T12:00:00Z",
                ),
            )

    history = list_invoice_reviews(
        "factura-003",
        limit=1,
        offset=1,
    )

    assert history["total"] == 3
    assert len(history["data"]) == 1
    assert history["data"][0]["notes"] == "Evento 1"


def test_history_query_is_parameterized(demo_database):
    review_invoice(
        "factura-003",
        "approve",
        USER_ID,
    )

    history = list_invoice_reviews(
        "factura-003' OR 1=1 --"
    )

    assert history["total"] == 0
    assert history["data"] == []
