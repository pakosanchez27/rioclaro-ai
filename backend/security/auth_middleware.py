
import json
import os
import azure.functions as func

from security.entra_auth import (
    validate_access_token,
    AuthenticationError,
)
from security.permissions import has_permission
from security.evaluator_auth import validate_session, EvaluatorAuthError

DEMO_PERMISSIONS = {
    "invoices:read",
    "invoices:stats",
    "invoices:analyze",
    "invoices:review",
    "assistant:ask",
    "complaints:read",
    "complaints:write",
    "reports:read",
}


def error_response(status_code: int, message: str):
    return func.HttpResponse(
        json.dumps({"error": message}),
        status_code=status_code,
        mimetype="application/json",
    )


def local_demo_enabled() -> bool:
    requested = os.getenv(
        "DEMO_MODE", "false"
    ).strip().lower() == "true"
    environment = os.getenv(
        "AZURE_FUNCTIONS_ENVIRONMENT",
        "Development",
    ).strip().lower()

    # No permitir que esta modalidad local se active
    # accidentalmente en Azure Functions desplegado.
    return (
        requested
        and environment == "development"
        and not os.getenv("WEBSITE_INSTANCE_ID")
    )


def authorize(req: func.HttpRequest, permission: str):
    demo_requested = os.getenv(
        "DEMO_MODE", "false"
    ).strip().lower() == "true"

    # Impedir un bypass accidental en producción.
    if demo_requested and not local_demo_enabled():
        return None, error_response(
            503,
            "Modo demostracion no disponible en este entorno.",
        )

    if local_demo_enabled():
        if permission not in DEMO_PERMISSIONS or not has_permission(
            ["analyst"], permission
        ):
            return None, error_response(
                403,
                "No tienes permisos para realizar esta operacion",
            )

        return {
            "user_id": "local-demo-analyst",
            "tenant_id": "local-demo",
            "username": "Demo Analyst",
            "roles": ["analyst"],
        }, None

    authorization = req.headers.get("Authorization", "")

    parts = authorization.strip().split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None, error_response(
            401,
            "Se requiere un token Bearer"
        )

    try:
        if parts[1].startswith("ev_"):
            user = validate_session(parts[1][3:])
        else:
            user = validate_access_token(parts[1])
    except EvaluatorAuthError:
        return None, error_response(401, "Sesion expirada")
    except AuthenticationError:
        return None, error_response(
            401,
            "Token de acceso invalido o expirado"
        )

    if not has_permission(user["roles"], permission):
        return None, error_response(
            403,
            "No tienes permisos para realizar esta operacion"
        )

    return user, None
