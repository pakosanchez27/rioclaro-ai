
ROLE_PERMISSIONS = {
    "admin": {
        "invoices:read",
        "invoices:analyze",
        "invoices:review",
        "invoices:stats",
        "settings:manage",
        "assistant:ask",
        "complaints:read",
        "complaints:write",
        "reports:read",
    },
    "analyst": {
        "invoices:read",
        "invoices:analyze",
        "invoices:review",
        "invoices:stats",
        "assistant:ask",
        "complaints:read",
        "complaints:write",
        "reports:read",
    },
    "viewer": {
        "invoices:read",
        "invoices:stats",
    },
}


def has_permission(roles: list[str], permission: str) -> bool:
    if not isinstance(roles, list):
        return False

    return any(
        permission in ROLE_PERMISSIONS.get(role, set())
        for role in roles
    )
