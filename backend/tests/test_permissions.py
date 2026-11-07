import pytest

from security.permissions import has_permission


@pytest.mark.parametrize(
    "role,permission,expected",
    [
        ("admin", "invoices:read", True),
        ("admin", "invoices:analyze", True),
        ("admin", "invoices:review", True),
        ("admin", "settings:manage", True),

        ("analyst", "invoices:read", True),
        ("analyst", "invoices:analyze", True),
        ("analyst", "invoices:review", True),
        ("analyst", "settings:manage", False),

        ("viewer", "invoices:read", True),
        ("viewer", "invoices:stats", True),
        ("viewer", "invoices:analyze", False),
        ("viewer", "invoices:review", False),

        ("unknown", "invoices:read", False),
    ],
)
def test_role_permissions(role, permission, expected):
    assert has_permission([role], permission) is expected


def test_no_roles():
    assert has_permission([], "invoices:read") is False


def test_multiple_roles():
    assert has_permission(
        ["viewer", "analyst"],
        "invoices:analyze",
    ) is True


def test_invalid_roles():
    assert has_permission(None, "invoices:read") is False