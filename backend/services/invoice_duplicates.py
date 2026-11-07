"""Deteccion determinista de documentos y facturas repetidos."""

import hashlib
import json
import re
import unicodedata
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from difflib import SequenceMatcher

from database.connection import get_connection
from database.table_storage import StorageConflictError


class DuplicateDocumentError(ValueError):
    def __init__(self, invoice_id: str | None):
        self.invoice_id = invoice_id
        super().__init__("Documento ya procesado" if invoice_id else "Documento en procesamiento")


class DuplicateBusinessError(ValueError):
    def __init__(self, related_invoice_id: str | None):
        self.related_invoice_id = related_invoice_id
        super().__init__("Factura de negocio duplicada" if related_invoice_id else "Factura de negocio en procesamiento")


def document_hash(document_bytes: bytes) -> str:
    return hashlib.sha256(document_bytes).hexdigest()


def claim_document(sha256: str) -> None:
    """Reserva el hash antes de llamar a servicios de IA."""
    try:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT invoice_id FROM invoice_document_claims WHERE sha256 = ?",
                (sha256,),
            ).fetchone()
            if row is not None:
                raise DuplicateDocumentError(row["invoice_id"])

            connection.execute(
                """INSERT INTO invoice_document_claims
                   (sha256, invoice_id, state, claimed_at)
                   VALUES (?, NULL, 'processing', ?)""",
                (sha256, datetime.now(timezone.utc).isoformat()),
            )
    except StorageConflictError as exc:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT invoice_id FROM invoice_document_claims WHERE sha256 = ?", (sha256,)
            ).fetchone()
        raise DuplicateDocumentError(row["invoice_id"] if row else None) from exc


def release_document(sha256: str) -> None:
    with get_connection() as connection:
        connection.execute(
            "DELETE FROM invoice_document_claims WHERE sha256 = ? AND state = 'processing'",
            (sha256,),
        )


def complete_document(connection, sha256: str, invoice_id: str) -> None:
    connection.execute(
        """UPDATE invoice_document_claims
           SET invoice_id = ?, state = 'completed'
           WHERE sha256 = ? AND state = 'processing'""",
        (invoice_id, sha256),
    )


def business_key(extraction: dict) -> str | None:
    amount = _amount(extraction.get("total"))
    fields = (
        _normalize(extraction.get("supplier_name")),
        _normalize(extraction.get("supplier_tax_id")),
        _normalize(extraction.get("invoice_number")),
        str(extraction.get("invoice_date") or ""),
        str(amount) if amount is not None else "",
        _normalize(extraction.get("currency")),
    )
    if not all((fields[0], fields[2], fields[3], fields[4], fields[5])):
        return None
    return hashlib.sha256(json.dumps(fields, separators=(",", ":")).encode()).hexdigest()


def claim_business_invoice(extraction: dict, document_sha256: str) -> str | None:
    key = business_key(extraction)
    if key is None:
        return None
    try:
        with get_connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT invoice_id FROM invoice_business_claims WHERE business_key = ?", (key,)
            ).fetchone()
            if row:
                raise DuplicateBusinessError(row["invoice_id"])
            connection.execute(
                """INSERT INTO invoice_business_claims
                   (business_key, document_sha256, invoice_id, state, claimed_at)
                   VALUES (?, ?, NULL, 'processing', ?)""",
                (key, document_sha256, datetime.now(timezone.utc).isoformat()),
            )
    except StorageConflictError as exc:
        with get_connection() as connection:
            row = connection.execute(
                "SELECT invoice_id FROM invoice_business_claims WHERE business_key = ?", (key,)
            ).fetchone()
        raise DuplicateBusinessError(row["invoice_id"] if row else None) from exc
    return key


def complete_business_invoice(connection, key: str | None, invoice_id: str) -> None:
    if key:
        connection.execute(
            """UPDATE invoice_business_claims SET invoice_id = ?, state = 'completed'
               WHERE business_key = ? AND state = 'processing'""",
            (invoice_id, key),
        )


def release_business_claim(document_sha256: str) -> None:
    with get_connection() as connection:
        connection.execute(
            """DELETE FROM invoice_business_claims
               WHERE document_sha256 = ? AND state = 'processing'""",
            (document_sha256,),
        )


def _normalize(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def _amount(value: object) -> Decimal | None:
    try:
        amount = Decimal(str(value))
        return amount.quantize(Decimal("0.01")) if amount.is_finite() else None
    except (InvalidOperation, TypeError, ValueError):
        return None


def find_business_duplicate(extraction: dict) -> dict:
    """Clasifica coincidencias sin tratar aproximaciones como certezas."""
    supplier = _normalize(extraction.get("supplier_name"))
    number = _normalize(extraction.get("invoice_number"))
    currency = _normalize(extraction.get("currency"))
    amount = _amount(extraction.get("total"))
    tax_id = _normalize(extraction.get("supplier_tax_id"))

    if not all((supplier, number, currency)) or amount is None:
        return {"status": "not_evaluable", "related_invoices": []}

    related = []
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT id, supplier_name, supplier_tax_id, invoice_number,
                      invoice_date, total, currency FROM invoices"""
        ).fetchall()

    for row in rows:
        row_supplier = _normalize(row["supplier_name"])
        row_number = _normalize(row["invoice_number"])
        row_currency = _normalize(row["currency"])
        row_amount = _amount(row["total"])
        row_tax_id = _normalize(row["supplier_tax_id"])

        if supplier != row_supplier or currency != row_currency or amount != row_amount:
            continue
        if tax_id and row_tax_id and tax_id != row_tax_id:
            continue

        same_date = bool(extraction.get("invoice_date")) and extraction.get("invoice_date") == row["invoice_date"]
        if number == row_number and same_date:
            related.append({"invoice_id": row["id"], "classification": "confirmed", "reason": "Proveedor, número, fecha, importe y moneda coinciden"})
        elif number == row_number or SequenceMatcher(None, number, row_number).ratio() >= 0.8:
            related.append({"invoice_id": row["id"], "classification": "possible", "reason": "Proveedor e importe coinciden; número o fecha requieren revisión"})
        else:
            related.append({"invoice_id": row["id"], "classification": "possible", "reason": "Proveedor e importe coinciden con otro número de factura"})

    status = "confirmed" if any(item["classification"] == "confirmed" for item in related) else "possible" if related else "none"
    return {"status": status, "related_invoices": related}
