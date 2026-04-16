from urllib.parse import urlencode

import requests
from flask import Blueprint, jsonify, request

from src.config import Config

auth_bp = Blueprint("auth", __name__)


@auth_bp.get("/config")
def auth_config():
    frontend_base = request.host_url.rstrip("/")

    return jsonify({
        "issuer": Config.KEYCLOAK_ISSUER,
        "realm": Config.KEYCLOAK_REALM,
        "client_id": "maga-frontend",
        "authorize_url": f"{Config.KEYCLOAK_PUBLIC_URL}/realms/{Config.KEYCLOAK_REALM}/protocol/openid-connect/auth",
        "token_url": f"{Config.KEYCLOAK_INTERNAL_URL}/realms/{Config.KEYCLOAK_REALM}/protocol/openid-connect/token",
        "logout_url": f"{Config.KEYCLOAK_PUBLIC_URL}/realms/{Config.KEYCLOAK_REALM}/protocol/openid-connect/logout",
        "redirect_uri": f"{frontend_base}/index.html"
    })


@auth_bp.post("/token")
def token():
    payload = request.get_json(silent=True) or {}
    grant_type = payload.get("grant_type", "authorization_code")

    token_url = (
        f"{Config.KEYCLOAK_INTERNAL_URL}/realms/"
        f"{Config.KEYCLOAK_REALM}/protocol/openid-connect/token"
    )

    data = {
        "client_id": "maga-frontend",
    }

    if grant_type == "authorization_code":
        code = payload.get("code")
        redirect_uri = payload.get("redirect_uri")
        code_verifier = payload.get("code_verifier")

        if not code or not redirect_uri:
            return jsonify({"error": "code and redirect_uri are required"}), 400

        data.update({
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
        })

        if code_verifier:
            data["code_verifier"] = code_verifier

    elif grant_type == "refresh_token":
        refresh_token = payload.get("refresh_token")

        if not refresh_token:
            return jsonify({"error": "refresh_token is required"}), 400

        data.update({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        })

    else:
        return jsonify({"error": "unsupported_grant_type"}), 400

    try:
        response = requests.post(token_url, data=data, timeout=20)
    except requests.RequestException as exc:
        return jsonify({
            "error": "token_request_failed",
            "details": str(exc),
        }), 502

    try:
        body = response.json()
    except Exception:
        body = {"error": "invalid_token_response", "raw": response.text}

    return jsonify(body), response.status_code


@auth_bp.post("/logout-url")
def build_logout_url():
    payload = request.get_json(silent=True) or {}
    post_logout_redirect_uri = payload.get("post_logout_redirect_uri")
    id_token_hint = payload.get("id_token_hint")

    if not post_logout_redirect_uri:
        return jsonify({"error": "post_logout_redirect_uri is required"}), 400

    base = (
        f"{Config.KEYCLOAK_PUBLIC_URL}/realms/"
        f"{Config.KEYCLOAK_REALM}/protocol/openid-connect/logout"
    )

    params = {
        "post_logout_redirect_uri": post_logout_redirect_uri
    }
    if id_token_hint:
        params["id_token_hint"] = id_token_hint

    return jsonify({
        "logout_url": f"{base}?{urlencode(params)}"
    })