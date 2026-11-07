import json

from database.connection import get_connection


def get_saved_invoice_analysis(invoice_id: str):
    """Consulta un analisis existente sin volver a llamar a Azure."""
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT
                invoice_id,
                extraction_json,
                analysis_json,
                created_at
            FROM invoice_analyses
            WHERE invoice_id = ?
            """,
            (invoice_id,),
        ).fetchone()

    if row is None:
        return None

    return {
        "invoice_id": row["invoice_id"],
        "extraction": json.loads(row["extraction_json"]),
        "analysis": json.loads(row["analysis_json"]),
        "created_at": row["created_at"],
    }
