
from database.connection import get_connection, initialize_database

DEMO_INVOICES = [
    (
        "factura-001", "Proveedor Demo A", None, "DEMO-001",
        "2026-11-01", "MXN", 1000.00, 160.00, 1160.00,
        "validated", "2026-11-01T12:00:00Z"
    ),
    (
        "factura-002", "Proveedor Demo B", None, "DEMO-002",
        "2026-11-02", "MXN", 1500.00, 240.00, 1740.00,
        "validated", "2026-11-02T12:00:00Z"
    ),
    (
        "factura-003", "Proveedor Demo C", None, "DEMO-003",
        "2026-11-03", "MXN", 2000.00, 320.00, 2320.00,
        "pending_review", "2026-11-03T12:00:00Z"
    ),
    (
        "factura-004", "Proveedor Demo D", None, "DEMO-004",
        "2026-11-04", "MXN", 1061.80, 0.00, 1061.80,
        "pending_review", "2026-11-04T12:00:00Z"
    ),
]


def seed_demo_data():
    initialize_database()

    with get_connection() as connection:
        connection.executemany(
            """
            INSERT OR IGNORE INTO invoices (
                id, supplier_name, supplier_tax_id,
                invoice_number, invoice_date, currency,
                subtotal, tax, total, status,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (*invoice, invoice[-1])
                for invoice in DEMO_INVOICES
            ],
        )


if __name__ == "__main__":
    seed_demo_data()
    print("Datos de demostracion cargados correctamente.")
