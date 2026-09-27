"""Authentication endpoints for the frontend session flow (issue #519).

- ``POST /auth/login``            - exchange an API key for a JWT pair
- ``POST /auth/refresh``          - rotate the refresh token
- ``POST /auth/logout``           - revoke the presented refresh token
- ``GET  /auth/me``               - current session user (roles + permissions)
- ``GET  /auth/oauth/{provider}/authorize`` - GitHub/Google OAuth2 (PKCE) start
- ``GET  /auth/oauth/{provider}/callback``  - OAuth2 callback -> one-time code
- ``POST /auth/exchange``         - swap the one-time code for a JWT pair

The API-key login reuses the existing :class:`InMemoryAuthProvider`
(``TASKER_AUTH_USERS`` / ``auth/users.json``) so CLI tokens double as
frontend credentials. OAuth requires ``TASKER_{GITHUB,GOOGLE}_CLIENT_ID/SECRET``.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode

import requests  # type: ignore[import-untyped]
from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from socialseed_tasker.auth import tokens
from socialseed_tasker.auth.auth import load_auth_provider

auth_router = APIRouter()

FRONTEND_URL = os.getenv("TASKER_FRONTEND_URL", "http://localhost:19001")
OAUTH_STATE_TTL = 600
EXCHANGE_CODE_TTL = 60

# state -> {provider, verifier, created_at} (OAuth) / code -> {user, created_at} (exchange)
_OAUTH_STATES: dict[str, dict[str, Any]] = {}
_EXCHANGE_CODES: dict[str, dict[str, Any]] = {}

_ROLE_FROM_PERMISSIONS = (
    ("admin", "ADMIN"),
    ("create:issue", "DEVELOPER"),
    ("delete:issue", "DEVELOPER"),
)

_DEFAULT_DEV_PERMISSIONS = ["create:issue", "delete:issue", "add:dependency", "read:context", "read:impact"]
_DEFAULT_VIEWER_PERMISSIONS = ["read:context", "read:impact"]


class LoginRequest(BaseModel):
    api_key: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class ExchangeRequest(BaseModel):
    code: str


def _role_for(permissions: list[str]) -> str:
    for perm, role in _ROLE_FROM_PERMISSIONS:
        if perm in permissions:
            return role
    return "VIEWER"


def _user_payload(user_id: str, permissions: list[str], username: str | None = None) -> dict[str, Any]:
    return {
        "id": user_id,
        "username": username or user_id,
        "role": _role_for(permissions),
        "permissions": sorted(set(permissions)),
    }


def _public_session(pair: dict[str, Any], user: dict[str, Any]) -> dict[str, Any]:
    return {**pair, "user": user}


def _sweep() -> None:
    now = time.time()
    for store in (_OAUTH_STATES, _EXCHANGE_CODES):
        for key in [k for k, v in store.items() if now - v["created_at"] > max(OAUTH_STATE_TTL, EXCHANGE_CODE_TTL)]:
            store.pop(key, None)


@auth_router.post("/auth/login", summary="Exchange an API key for a JWT session")
def login(body: LoginRequest) -> dict[str, Any]:
    provider = load_auth_provider()
    user_id = provider.verify_token(body.api_key)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    info = provider.get_user_info(user_id) or {}
    permissions = list(info.get("permissions") or _DEFAULT_VIEWER_PERMISSIONS)
    user = _user_payload(user_id, permissions, username=info.get("username", user_id))
    return _public_session(tokens.issue_tokens(user), user)


@auth_router.post("/auth/refresh", summary="Rotate the refresh token")
def refresh(body: RefreshRequest) -> dict[str, Any]:
    claims = tokens.peek(body.refresh_token)
    if claims is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    pair = tokens.rotate(body.refresh_token)
    if pair is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = _user_payload(
        claims.get("sub", "unknown"),
        list(claims.get("permissions") or []),
        username=claims.get("username"),
    )
    return _public_session(pair, user)


@auth_router.post("/auth/logout", summary="Revoke a refresh token")
def logout(body: LogoutRequest) -> dict[str, Any]:
    if body.refresh_token:
        tokens.revoke(body.refresh_token)
    return {"ok": True}


@auth_router.get("/auth/me", summary="Current session user")
def me(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    claims = tokens.verify_access(authorization[7:])
    if claims is None:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    return {
        "id": claims.get("sub"),
        "username": claims.get("username"),
        "role": claims.get("role", "VIEWER"),
        "permissions": claims.get("permissions", []),
    }


# ---------------------------------------------------------------- OAuth2 PKCE

_PROVIDERS = {
    "github": {
        "authorize": "https://github.com/login/oauth/authorize",
        "token": "https://github.com/login/oauth/access_token",
        "profile": "https://api.github.com/user",
        "emails": "https://api.github.com/user/emails",
        "scope": "read:user user:email",
    },
    "google": {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "profile": "https://openidconnect.googleapis.com/v1/userinfo",
        "scope": "openid email profile",
    },
}


def _oauth_config(provider: str) -> dict[str, Any]:
    meta = _PROVIDERS.get(provider)
    if meta is None:
        raise HTTPException(status_code=404, detail=f"Unknown provider '{provider}'")
    client_id = os.getenv(f"{provider.upper()}_CLIENT_ID", "")
    client_secret = os.getenv(f"{provider.upper()}_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=403,
            detail=f"oauth_not_configured:{provider}",
        )
    return {**meta, "client_id": client_id, "client_secret": client_secret}


@auth_router.get("/auth/oauth/{provider}/authorize", summary="Start an OAuth2 (PKCE) login")
def oauth_authorize(provider: str) -> dict[str, Any]:
    _sweep()
    cfg = _oauth_config(provider)
    state = secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    _OAUTH_STATES[state] = {"provider": provider, "verifier": verifier, "created_at": time.time()}
    redirect_uri = f"{FRONTEND_URL.rstrip('/')}/auth/oauth-callback"
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": redirect_uri,
        "scope": cfg["scope"],
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    if provider == "github":
        params["response_type"] = "code"
    else:
        params["response_type"] = "code"
        params["access_type"] = "offline"
    separator = "&" if "?" in cfg["authorize"] else "?"
    return {"authorize_url": cfg["authorize"] + separator + urlencode(params), "state": state}


@auth_router.get("/auth/oauth/{provider}/callback", summary="OAuth2 callback -> frontend one-time code")
def oauth_callback(provider: str, code: str, state: str) -> RedirectResponse:
    _sweep()
    pending = _OAUTH_STATES.pop(state, None)
    if pending is None or pending["provider"] != provider:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")
    cfg = _oauth_config(provider)
    redirect_uri = f"{FRONTEND_URL.rstrip('/')}/auth/oauth-callback"
    try:
        token_resp = requests.post(
            cfg["token"],
            data={
                "client_id": cfg["client_id"],
                "client_secret": cfg["client_secret"],
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": pending["verifier"],
            },
            headers={"Accept": "application/json"},
            timeout=10,
        )
        token_resp.raise_for_status()
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="OAuth token exchange failed")
        profile_resp = requests.get(
            cfg["profile"],
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
            timeout=10,
        )
        profile_resp.raise_for_status()
        profile = profile_resp.json()
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - surface provider errors as 400
        raise HTTPException(status_code=400, detail=f"OAuth provider error: {exc}") from exc

    if provider == "github":
        identity = str(profile.get("id"))
        username = profile.get("login") or f"github-{identity}"
        email = profile.get("email")
        if not email:
            try:
                emails = requests.get(
                    cfg["emails"],
                    headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                    timeout=10,
                ).json()
                primary = next((e for e in emails if e.get("primary") and e.get("verified")), None)
                email = (primary or (emails[0] if emails else {})).get("email")
            except Exception:
                email = None
    else:
        identity = str(profile.get("sub"))
        username = (
            profile.get("preferred_username") or profile.get("name") or profile.get("email") or f"google-{identity}"
        )
        email = profile.get("email")

    # Map to local roles: org admins by email suffix can be promoted via env.
    admin_emails = {e.strip() for e in os.getenv("TASKER_AUTH_ADMIN_EMAILS", "").split(",") if e.strip()}
    role = "ADMIN" if email in admin_emails else "DEVELOPER"
    permissions = list(_DEFAULT_DEV_PERMISSIONS) + (["admin"] if role == "ADMIN" else [])
    user = _user_payload(f"oauth:{provider}:{identity}", permissions, username=username)
    user["email"] = email

    one_time = secrets.token_urlsafe(32)
    _EXCHANGE_CODES[one_time] = {"user": user, "created_at": time.time()}
    return RedirectResponse(f"{FRONTEND_URL.rstrip('/')}/auth/oauth-callback?code={one_time}")


@auth_router.post("/auth/exchange", summary="Swap the one-time OAuth code for a JWT pair")
def exchange(body: ExchangeRequest) -> dict[str, Any]:
    _sweep()
    entry = _EXCHANGE_CODES.pop(body.code, None)
    if entry is None:
        raise HTTPException(status_code=401, detail="Invalid or expired authorization code")
    user = entry["user"]
    return _public_session(tokens.issue_tokens(user), user)
