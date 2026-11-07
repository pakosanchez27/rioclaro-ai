"""Registro y consulta de quejas ficticias."""

import uuid
from datetime import datetime, timezone

from database.connection import get_connection


class ComplaintInputError(ValueError):
    pass


def create_complaint(order_folio: str, branch_code: str, message: str, category: str) -> dict:
    if not isinstance(order_folio, str) or not order_folio.strip():
        raise ComplaintInputError("Selecciona un pedido")
    if not isinstance(branch_code, str) or not branch_code.strip():
        raise ComplaintInputError("Selecciona una sucursal")
    if not isinstance(message, str) or not 10 <= len(message.strip()) <= 1000:
        raise ComplaintInputError("Describe el problema en 10 a 1000 caracteres")
    if category not in ("delivery", "product", "service", "other"):
        raise ComplaintInputError("Categoría inválida")

    folio = "QUE-" + uuid.uuid4().hex[:12].upper()
    created_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with get_connection() as connection:
        branch = connection.execute(
            "SELECT id FROM branches WHERE code = ? AND status = 'active'",
            (branch_code.strip().upper(),),
        ).fetchone()
        if branch is None:
            raise ComplaintInputError("Sucursal no encontrada")
        order = connection.execute(
            "SELECT folio, branch_id FROM orders WHERE folio = ?",
            (order_folio.strip().upper(),),
        ).fetchone()
        if order is None or order["branch_id"] != branch["id"]:
            raise ComplaintInputError("El pedido no corresponde a la sucursal")
        connection.execute(
            """INSERT INTO complaints
               (folio, customer_name, order_folio, branch_id, message, category,
                status, created_at, updated_at)
               VALUES (?, 'Cliente Demo', ?, ?, ?, ?, 'open', ?, ?)""",
            (folio, order["folio"], branch["id"], message.strip(), category, created_at, created_at),
        )
    return {"folio": folio, "status": "open", "created_at": created_at}


def get_complaint(folio: str):
    with get_connection() as connection:
        row = connection.execute(
            """SELECT c.folio, c.order_folio, b.name AS branch_name, c.message,
                      c.category, c.status, c.created_at, c.updated_at
               FROM complaints c JOIN branches b ON b.id = c.branch_id
               WHERE c.folio = ?""",
            (folio.strip().upper(),),
        ).fetchone()
    return dict(row) if row else None
