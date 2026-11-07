from datetime import datetime, timezone

from database.connection import get_connection
from database.table_storage import StorageConflictError


class ReviewValidationError(Exception):
    pass


class InvoiceNotFoundError(Exception):
    pass


class InvoiceAlreadyReviewedError(Exception):
    pass


def _review_invoice_once(
    invoice_id: str,
    decision: str,
    actor_oid: str,
    notes: str | None = None,
) -> dict:

    # Validaciones de entrada
    if not isinstance(invoice_id, str) or not invoice_id.strip():
        raise ReviewValidationError(
            "El identificador de factura es obligatorio"
        )

    if not isinstance(decision, str) or decision not in (
        "approve", "reject"
    ):
        raise ReviewValidationError(
            "La decision debe ser approve o reject"
        )

    if not isinstance(actor_oid, str) or not actor_oid.strip():
        raise ReviewValidationError(
            "No se pudo identificar al usuario"
        )

    if notes is not None and not isinstance(notes, str):
        raise ReviewValidationError(
            "Las observaciones deben ser texto"
        )

    invoice_id = invoice_id.strip()
    notes = (notes or "").strip()

    if len(notes) > 1000:
        raise ReviewValidationError(
            "Las observaciones no pueden superar 1000 caracteres"
        )

    if decision == "reject" and not notes:
        raise ReviewValidationError(
            "Es obligatorio indicar el motivo del rechazo"
        )

    new_status = (
        "validated" if decision == "approve" else "rejected"
    )

    reviewed_at = datetime.now(
        timezone.utc
    ).isoformat().replace("+00:00", "Z")

    with get_connection() as connection:

        # Serializar revisiones simultaneas en SQLite
        connection.execute("BEGIN IMMEDIATE")

        invoice = connection.execute(
            """
            SELECT id, status
            FROM invoices
            WHERE id = ?
            """,
            (invoice_id,),
        ).fetchone()

        if invoice is None:
            raise InvoiceNotFoundError(
                "Factura no encontrada"
            )

        previous_status = invoice["status"]

        if previous_status != "pending_review":
            raise InvoiceAlreadyReviewedError(
                "La factura no esta pendiente de revision"
            )

        # Actualizar la factura
        updated = connection.execute(
            """
            UPDATE invoices
            SET status = ?, updated_at = ?
            WHERE id = ? AND status = 'pending_review'
            """,
            (new_status, reviewed_at, invoice_id),
        )

        if updated.rowcount != 1:
            raise InvoiceAlreadyReviewedError(
                "No se pudo actualizar el estado de la factura"
            )

        # Registrar la auditoria dentro de la misma transaccion
        cursor = connection.execute(
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
                invoice_id,
                decision,
                previous_status,
                new_status,
                notes,
                actor_oid,
                reviewed_at,
            ),
        )

        review_id = cursor.lastrowid

    return {
        "review_id": review_id,
        "invoice_id": invoice_id,
        "decision": decision,
        "previous_status": previous_status,
        "status": new_status,
        "notes": notes,
        "reviewed_by": actor_oid,
        "reviewed_at": reviewed_at,
    }


def review_invoice(invoice_id: str, decision: str, actor_oid: str,
                   notes: str | None = None) -> dict:
    try:
        return _review_invoice_once(invoice_id, decision, actor_oid, notes)
    except StorageConflictError:
        # La otra revisión pudo haber ganado la escritura condicional.
        # Una lectura nueva decide si corresponde 409 o reintentar.
        try:
            return _review_invoice_once(invoice_id, decision, actor_oid, notes)
        except StorageConflictError as exc:
            raise InvoiceAlreadyReviewedError("Revision concurrente; actualiza la factura") from exc
