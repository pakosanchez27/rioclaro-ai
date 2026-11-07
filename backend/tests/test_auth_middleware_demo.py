import azure.functions as func
import pytest

from security import auth_middleware


@pytest.fixture
def http_request():
    return func.HttpRequest(
        method="GET",
        url="http://localhost/api/invoices",
        body=b"",
    )


@pytest.fixture
def local_demo(monkeypatch):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", "Development")
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)


@pytest.mark.parametrize("permission", sorted(auth_middleware.DEMO_PERMISSIONS))
def test_local_demo_allows_analyst_permissions(local_demo, http_request, permission):
    user, error = auth_middleware.authorize(http_request, permission)

    assert error is None
    assert user["roles"] == ["analyst"]
    assert user["user_id"] == "local-demo-analyst"


def test_local_demo_cannot_manage_settings(local_demo, http_request):
    user, error = auth_middleware.authorize(http_request, "settings:manage")

    assert user is None
    assert error.status_code == 403


@pytest.mark.parametrize(
    "environment,instance_id",
    [("Production", None), ("Development", "azure-instance")],
)
def test_demo_request_rejected_outside_local_development(
    monkeypatch, http_request, environment, instance_id
):
    monkeypatch.setenv("DEMO_MODE", "true")
    monkeypatch.setenv("AZURE_FUNCTIONS_ENVIRONMENT", environment)
    if instance_id is None:
        monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    else:
        monkeypatch.setenv("WEBSITE_INSTANCE_ID", instance_id)

    user, error = auth_middleware.authorize(http_request, "invoices:read")

    assert user is None
    assert error.status_code == 503


def test_demo_disabled_still_requires_bearer_token(monkeypatch, http_request):
    monkeypatch.setenv("DEMO_MODE", "false")

    user, error = auth_middleware.authorize(http_request, "invoices:read")

    assert user is None
    assert error.status_code == 401
