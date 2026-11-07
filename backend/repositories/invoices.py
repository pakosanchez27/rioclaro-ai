from database.connection import get_connection


def list_invoices(limit=50, offset=0):
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT *
            FROM invoices
            ORDER BY created_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()

    return [dict(row) for row in rows]


def get_invoice(invoice_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM invoices WHERE id = ?",
            (invoice_id,),
        ).fetchone()

    return dict(row) if row else None


def get_invoice_stats():
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                COUNT(*) AS total_invoices,
                COALESCE(SUM(total), 0) AS total_amount,
                SUM(CASE WHEN status = 'validated'
                    THEN 1 ELSE 0 END) AS validated,
                SUM(CASE WHEN status = 'pending_review'
                    THEN 1 ELSE 0 END) AS pending_review
            FROM invoices
            """
        ).fetchone()

    return dict(row)