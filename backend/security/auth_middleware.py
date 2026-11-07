
import json
import azure.functions as func

from security.entra_auth import (
    validate_access_token,
    AuthenticationError,
)
from security.permissions import has_permission


def error_response(status_code: int, message: str):
    return func.HttpResponse(
        json.dumps({"error": message}),
        status_code=status_code,
        mimetype="application/json",
    )


def authorize(req: func.HttpRequest, permission: str):
    authorization = req.headers.get("Authorization", "")

    parts = authorization.strip().split()

    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None, error_response(
            401,
            "Se requiere un token Bearer"
        )

    try:
        user = validate_access_token(parts[1])
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
