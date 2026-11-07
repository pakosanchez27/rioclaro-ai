"""Datos ficticios e idempotentes para la demostracion empresarial."""

from database.connection import get_connection, initialize_database


BRANCHES = [
    ("gdl", "GDL", "Guadalajara", "Guadalajara", "Jalisco", "active"),
    ("zap", "ZAP", "Zapopan", "Zapopan", "Jalisco", "active"),
    ("leo", "LEO", "León", "León", "Guanajuato", "active"),
    ("qro", "QRO", "Querétaro", "Querétaro", "Querétaro", "active"),
    ("ags", "AGS", "Aguascalientes", "Aguascalientes", "Aguascalientes", "active"),
]

PRODUCTS = [
    ("cloro-1l", "LIM-001", "Cloro 1 L", "Blanqueador líquido de un litro", "Limpieza", "pieza", 24.50, "MXN", "active"),
    ("detergente-5l", "LIM-002", "Detergente industrial 5 L", "Detergente líquido industrial", "Limpieza", "garrafa", 189.00, "MXN", "active"),
    ("desinfectante-1l", "LIM-003", "Desinfectante 1 L", "Desinfectante para superficies", "Higiene", "pieza", 39.00, "MXN", "active"),
]

ALIASES = [
    ("cloro1l", "Cloro 1L", "cloro-1l"),
    ("clorolitro", "CLORO LITRO", "cloro-1l"),
    ("blanqueador1000ml", "Blanqueador 1000ml", "cloro-1l"),
    ("detergenteindustrial", "Detergente industrial", "detergente-5l"),
    ("desinfectante", "Desinfectante", "desinfectante-1l"),
]

UPDATED_AT = "2026-11-07T12:00:00Z"


def seed_business_demo_data() -> None:
    initialize_database()
    with get_connection() as connection:
        connection.executemany(
            "INSERT OR IGNORE INTO branches VALUES (?, ?, ?, ?, ?, ?)",
            BRANCHES,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            PRODUCTS,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO product_aliases VALUES (?, ?, ?)",
            ALIASES,
        )
        inventory = [
            (product, branch, quantity, UPDATED_AT, "available" if quantity else "out_of_stock")
            for product, amounts in {
                "cloro-1l": [90, 75, 42, 60, 38],
                "detergente-5l": [25, 16, 8, 18, 12],
                "desinfectante-1l": [55, 31, 20, 68, 14],
            }.items()
            for branch, quantity in zip(("gdl", "zap", "leo", "qro", "ags"), amounts)
        ]
        connection.executemany(
            "INSERT OR IGNORE INTO inventory VALUES (?, ?, ?, ?, ?)",
            inventory,
        )
        connection.executemany(
            "INSERT OR IGNORE INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                ("PED-001", "Cliente Demo 001", "leo", "2026-11-05", "pending", 245.00, "MXN", UPDATED_AT),
                ("PED-002", "Cliente Demo 002", "gdl", "2026-11-06", "delivered", 189.00, "MXN", UPDATED_AT),
                ("PED-003", "Cliente Demo 003", "qro", "2026-11-07", "pending", 156.00, "MXN", UPDATED_AT),
            ],
        )
        connection.executemany(
            "INSERT OR IGNORE INTO order_items VALUES (?, ?, ?, ?)",
            [
                ("PED-001", "cloro-1l", 10, 24.50),
                ("PED-002", "detergente-5l", 1, 189.00),
                ("PED-003", "desinfectante-1l", 4, 39.00),
            ],
        )
        connection.executemany(
            "INSERT OR IGNORE INTO policies VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                ("devoluciones", 1, "Devoluciones", "Atención al cliente", "Versión histórica: consultar la política vigente.", "2025-01-01", "obsolete"),
                ("devoluciones", 2, "Devoluciones", "Atención al cliente", "Se reciben solicitudes de devolución hasta 30 días después de la entrega, sujetas a revisión humana y comprobante de compra.", "2026-01-01", "current"),
            ],
        )


if __name__ == "__main__":
    seed_business_demo_data()
