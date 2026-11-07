"""Consultas de solo lectura sobre datos empresariales ficticios."""

import re
import unicodedata

from database.connection import get_connection


def normalize_key(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]", "", text.lower())


def find_product(query: str):
    key = normalize_key(query)
    if not key:
        return None
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM products WHERE status = 'active'"
        ).fetchall()
        for row in rows:
            if key in (normalize_key(row["name"]), normalize_key(row["sku"])):
                return dict(row)
        alias = connection.execute(
            "SELECT product_id FROM product_aliases WHERE alias_key = ?",
            (key,),
        ).fetchone()
        if alias:
            row = connection.execute(
                "SELECT * FROM products WHERE id = ? AND status = 'active'",
                (alias["product_id"],),
            ).fetchone()
            return dict(row) if row else None
    return None


def find_branch(query: str):
    key = normalize_key(query)
    if not key:
        return None
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM branches WHERE status = 'active'").fetchall()
    return next((dict(row) for row in rows if key in (
        normalize_key(row["code"]), normalize_key(row["name"]), normalize_key(row["city"])
    )), None)


def get_inventory(product_query: str, branch_query: str | None = None):
    product = find_product(product_query)
    if product is None:
        return None
    branch = find_branch(branch_query) if branch_query else None
    if branch_query and branch is None:
        return None
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT i.quantity, i.updated_at, i.status,
                      b.id AS branch_id, b.name AS branch_name
               FROM inventory i JOIN branches b ON b.id = i.branch_id
               WHERE i.product_id = ? AND (? IS NULL OR b.id = ?)
               ORDER BY i.quantity DESC, b.name""",
            (product["id"], branch["id"] if branch else None, branch["id"] if branch else None),
        ).fetchall()
    return {"product": product, "inventory": [dict(row) for row in rows]}


def get_order(folio: str):
    with get_connection() as connection:
        row = connection.execute(
            """SELECT o.*, b.name AS branch_name FROM orders o
               JOIN branches b ON b.id = o.branch_id WHERE o.folio = ?""",
            (folio.strip().upper(),),
        ).fetchone()
        if row is None:
            return None
        items = connection.execute(
            """SELECT p.sku, p.name, oi.quantity, oi.unit_price
               FROM order_items oi JOIN products p ON p.id = oi.product_id
               WHERE oi.order_folio = ?""",
            (row["folio"],),
        ).fetchall()
    return {**dict(row), "items": [dict(item) for item in items]}


def get_current_policy(category: str):
    key = normalize_key(category)
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM policies WHERE status = 'current' ORDER BY version DESC"
        ).fetchall()
    return next((dict(row) for row in rows if key in (
        normalize_key(row["id"]), normalize_key(row["title"]), normalize_key(row["category"])
    )), None)


def get_low_stock_products(threshold: int = 20):
    if not 0 <= threshold <= 1000:
        raise ValueError("Umbral de existencias invalido")
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT p.sku, p.name AS product_name, b.name AS branch_name,
                      i.quantity, i.updated_at FROM inventory i
               JOIN products p ON p.id = i.product_id
               JOIN branches b ON b.id = i.branch_id
               WHERE i.quantity <= ? ORDER BY i.quantity, b.name LIMIT 50""",
            (threshold,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_pending_orders():
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT o.folio, o.status, o.total, o.currency, o.updated_at,
                      b.name AS branch_name FROM orders o
               JOIN branches b ON b.id = o.branch_id
               WHERE o.status = 'pending' ORDER BY o.order_date DESC LIMIT 50"""
        ).fetchall()
    return [dict(row) for row in rows]


def get_demo_options():
    with get_connection() as connection:
        branches = connection.execute(
            "SELECT code, name FROM branches WHERE status = 'active' ORDER BY name"
        ).fetchall()
        orders = connection.execute(
            """SELECT o.folio, b.code AS branch_code FROM orders o
               JOIN branches b ON b.id = o.branch_id ORDER BY o.folio"""
        ).fetchall()
    return {"branches": [dict(row) for row in branches], "orders": [dict(row) for row in orders]}


def get_branch_report():
    with get_connection() as connection:
        rows = connection.execute(
            """SELECT b.code, b.name,
                      COALESCE(SUM(CASE WHEN o.status = 'delivered' THEN o.total ELSE 0 END), 0) AS delivered_sales,
                      SUM(CASE WHEN o.status = 'pending' THEN 1 ELSE 0 END) AS pending_orders,
                      MAX(o.updated_at) AS updated_at
               FROM branches b LEFT JOIN orders o ON o.branch_id = b.id
               WHERE b.status = 'active' GROUP BY b.id ORDER BY b.name"""
        ).fetchall()
        products = connection.execute(
            """SELECT p.sku, p.name, SUM(oi.quantity) AS units_sold
               FROM order_items oi JOIN orders o ON o.folio = oi.order_folio
               JOIN products p ON p.id = oi.product_id
               WHERE o.status = 'delivered' GROUP BY p.id ORDER BY units_sold DESC"""
        ).fetchall()
    return {
        "branches": [dict(row) for row in rows],
        "products_sold": [dict(row) for row in products],
        "currency": "MXN",
        "data_label": "Datos ficticios de demostración",
    }
