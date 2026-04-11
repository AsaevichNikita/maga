import time
from functools import wraps

import jwt
from flask import current_app, g, jsonify, request
from jwt import PyJWKClient


_jwks_cache = {
    "client": None,
    "url": None,
    "created_at": 0,
}


def _get_jwk_client():
    jwks_url = current_app.config["KEYCLOAK_JWKS_URL"]

    if (
        _jwks_cache["client"] is None
        or _jwks_cache["url"] != jwks_url
        or time.time() - _jwks_cache["created_at"] > 600
    ):
        _jwks_cache["client"] = PyJWKClient(jwks_url)
        _jwks_cache["url"] = jwks_url
        _jwks_cache["created_at"] = time.time()

    return _jwks_cache["client"]


def _extract_bearer_token():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()


def _get_expected_audiences() -> list[str]:
    raw = str(current_app.config.get("KEYCLOAK_AUDIENCE", "") or "")
    items = [x.strip() for x in raw.replace(";", ",").split(",") if x.strip()]

    client_id = str(current_app.config.get("KEYCLOAK_CLIENT_ID", "") or "").strip()
    if client_id and client_id not in items:
        items.append(client_id)

    return items


def decode_keycloak_token(token: str) -> dict:
    jwk_client = _get_jwk_client()
    signing_key = jwk_client.get_signing_key_from_jwt(token)

    issuer = current_app.config["KEYCLOAK_ISSUER"]
    audiences = _get_expected_audiences()

    decode_kwargs = {
        "algorithms": ["RS256"],
        "issuer": issuer,
        "options": {"verify_aud": bool(audiences)},
    }
    if audiences:
        decode_kwargs["audience"] = audiences

    payload = jwt.decode(token, signing_key.key, **decode_kwargs)
    return payload


def get_roles_from_payload(payload: dict) -> list[str]:
    realm_access = payload.get("realm_access", {})
    return realm_access.get("roles", [])


def populate_keycloak_context(payload: dict) -> dict:
    g.keycloak_token = payload
    g.keycloak_roles = get_roles_from_payload(payload)
    g.keycloak_user = {
        "sub": payload.get("sub"),
        "preferred_username": payload.get("preferred_username"),
        "email": payload.get("email"),
        "roles": g.keycloak_roles,
    }
    return payload


def try_keycloak_authentication():
    token = _extract_bearer_token()
    if not token:
        return None

    payload = decode_keycloak_token(token)
    return populate_keycloak_context(payload)


def keycloak_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        token = _extract_bearer_token()
        if not token:
            return jsonify({"error": "Missing bearer token"}), 401

        try:
            payload = decode_keycloak_token(token)
        except Exception as exc:
            return jsonify({"error": "Invalid token", "details": str(exc)}), 401

        populate_keycloak_context(payload)
        return fn(*args, **kwargs)

    return wrapper


def roles_required(*required_roles):
    def decorator(fn):
        @wraps(fn)
        @keycloak_required
        def wrapper(*args, **kwargs):
            user_roles = set(g.keycloak_roles or [])
            needed = set(required_roles)

            if not user_roles.intersection(needed):
                return jsonify({
                    "error": "Forbidden",
                    "required_roles": list(needed),
                    "user_roles": list(user_roles),
                }), 403

            return fn(*args, **kwargs)

        return wrapper

    return decorator
