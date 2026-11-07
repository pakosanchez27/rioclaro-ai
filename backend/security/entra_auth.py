
import os
import jwt
from jwt import PyJWKClient
from functools import lru_cache


class AuthenticationError(Exception):
    pass


@lru_cache(maxsize=4)
def get_jwks_client(tenant_id: str):
    url = (
        f"https://login.microsoftonline.com/"
        f"{tenant_id}/discovery/v2.0/keys"
    )
    return PyJWKClient(url)


def validate_access_token(token: str) -> dict:
    tenant_id = os.getenv("ENTRA_TENANT_ID")
    audience = os.getenv("ENTRA_API_AUDIENCE")

    if not tenant_id or not audience:
        raise AuthenticationError(
            "La autenticacion de la API no esta configurada"
        )

    issuer = (
        f"https://login.microsoftonline.com/"
        f"{tenant_id}/v2.0"
    )

    try:
        signing_key = get_jwks_client(
            tenant_id
        ).get_signing_key_from_jwt(token)

        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=audience,
            issuer=issuer,
            options={
                "require": [
                    "exp", "iat", "nbf",
                    "iss", "aud", "tid", "oid", "ver"
                ]
            }
        )

        if claims.get("tid") != tenant_id:
            raise AuthenticationError("Tenant no autorizado")

        if claims.get("ver") != "2.0":
            raise AuthenticationError("Version de token no admitida")

        roles = claims.get("roles", [])

        if not isinstance(roles, list):
            raise AuthenticationError("Formato de roles invalido")

        return {
            "user_id": claims["oid"],
            "tenant_id": claims["tid"],
            "username": claims.get(
                "preferred_username",
                claims.get("name", "")
            ),
            "roles": roles,
        }

    except jwt.PyJWTError as exc:
        raise AuthenticationError(
            "Token invalido o expirado"
        ) from exc
