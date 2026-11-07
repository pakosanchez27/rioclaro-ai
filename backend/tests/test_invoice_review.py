import pytest

from database.connection import get_connection
from repositories.invoices import get_invoice
from seed_demo import seed_demo_data
from services.invoice_review import (
    review_invoice,
    ReviewValidationError,
    InvoiceNotFoundError,
    InvoiceAlreadyReviewedError,
)


USER_ID = "usuario-test-001"


@pytest.fixture
def demo_database(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "SQLITE_DB_PATH",
        str(tmp_path / "review_test.db"),
    )
    seed_demo_data()


def test_approve_invoice(demo_database):
    result = review_invoice(
        "factura-003",
        "approve",
        USER_ID,
        "Factura verificada",
    )

    assert result["status"] == "validated"
    assert get_invoice("factura-003")["status"] == "validated"


def test_reject_invoice(demo_database):
    result = review_invoice(
        "factura-004",
        "reject",
        USER_ID,
        "Importe incorrecto",
    )

    assert result["status"] == "rejected"
    assert get_invoice("factura-004")["status"] == "rejected"


def test_reject_requires_notes(demo_database):
    with pytest.raises(ReviewValidationError):
        review_invoice(
            "factura-004",
            "reject",
            USER_ID,
        )

    assert get_invoice("factura-004")["status"] == "pending_review"


def test_invoice_not_found(demo_database):
    with pytest.raises(InvoiceNotFoundError):
        review_invoice(
            "inexistente",
            "approve",
            USER_ID,
        )


def test_prevent_double_review(demo_database):
    review_invoice(
        "factura-003",
        "approve",
        USER_ID,
    )

    with pytest.raises(InvoiceAlreadyReviewedError):
        review_invoice(
            "factura-003",
            "reject",
            USER_ID,
            "Segundo intento",
        )


def test_invalid_decision(demo_database):
    with pytest.raises(ReviewValidationError):
        review_invoice(
            "factura-003",
            "delete",
            USER_ID,
        )


def test_review_audit(demo_database):
    review_invoice(
        "factura-003",
        "approve",
        USER_ID,
        "Validacion correcta",
    )

    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT *
            FROM invoice_reviews
            WHERE invoice_id = ?
            """,
            ("factura-003",),
        ).fetchone()

    assert row is not None
    assert row["reviewed_by_oid"] == USER_ID
    assert row["previous_status"] == "pending_review"
    assert row["new_status"] == "validated"
    assert row["reviewed_at"]


def test_failed_review_does_not_create_audit(demo_database):
    with pytest.raises(ReviewValidationError):
        review_invoice(
            "factura-004",
            "reject",
            USER_ID,
            "",
        )

    with get_connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM invoice_reviews"
        ).fetchone()[0]

    assert count == 0