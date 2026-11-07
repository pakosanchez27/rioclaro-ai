
from database.connection import get_connection


def list_invoice_reviews(
    invoice_id: str,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """
    Consulta el historial de revisiones de una factura.
    No modifica los registros de auditoria.
    """

    with get_connection() as connection:
        total = connection.execute(
            """
            SELECT COUNT(*)
            FROM invoice_reviews
            WHERE invoice_id = ?
            """,
            (invoice_id,),
        ).fetchone()[0]

        rows = connection.execute(
            """
            SELECT
                id,
                invoice_id,
                decision,
                previous_status,
                new_status,
                notes,
                reviewed_by_oid,
                reviewed_at
            FROM invoice_reviews
            WHERE invoice_id = ?
            ORDER BY reviewed_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (invoice_id, limit, offset),
        ).fetchall()

    return {
        "data": [dict(row) for row in rows],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
