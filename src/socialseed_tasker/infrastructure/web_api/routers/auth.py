"""Authentication endpoints for the frontend session flow (issues #519, #527).

- ``POST /auth/login``            - username/password (PostgreSQL + bcrypt) or
  API key -> JWT pair backed by a Redis session
- ``POST /auth/refresh``          - rotate the refresh token and renew the session
- ``POST /auth/logout``           - revoke the session and the presented refresh token
- ``GET  /auth/me``               - current session user (roles + permissions)
- ``GET  /auth/oauth/{provider}/authorize`` - GitHub/Google OAuth2 (PKCE) start
- ``GET  /auth/oauth/{provider}/callback``  - OAuth2 callback -> one-time code
- ``POST /auth/exchange``         - swap the one-time code for a JWT pair

Password login normalizes the username (issue #526) and validates the bcrypt
hash in ``users`` (``TASKER_DATABASE_URL``); the API-key login reuses
:class:`InMemoryAuthProvider` (``TASKER_AUTH_USERS`` / ``auth/users.json``) so
CLI tokens double as frontend credentials and also accepts the setup-wizard
master key as an admin session (notas.md #3). Every JWT pair carries a ``sid``
session id persisted under ``session:{user_id}:{session_id}`` in Redis with a
TTL equal to the refresh lifetime; logout deletes that key and refresh fails
once the session is gone (issue #527). OAuth requires
``TASKER_{GITHUB,GOOGLE}_CLIENT_ID/SECRET``.
"""

from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
import uuid
from typing import Any
from urllib.parse import urlencode

import requests  # type: ignore[import-untyped]
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from socialseed_tasker.auth import tokens
from socialseed_tasker.auth.auth import load_auth_provider
from socialseed_tasker.auth.redis_sessions import AuthSessionStore
from socialseed_tasker.auth.user_store import authenticate_user
from socialseed_tasker.config.storage import get_database_url

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
    api_key: str | None = None
    username: str | None = None
    password: str | None = None


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


def _permissions_for_db_role(role: Any) -> list[str]:
    value = str(role or "").strip().lower()
    if "admin" in value:
        return sorted(set(_DEFAULT_DEV_PERMISSIONS + ["admin"]))
    if value in ("lead-developer", "developer", "ai-agent"):
        return list(_DEFAULT_DEV_PERMISSIONS)
    return list(_DEFAULT_VIEWER_PERMISSIONS)


def _session_store(request: Request) -> AuthSessionStore:
    store = getattr(request.app.state, "auth_sessions", None)
    if store is None:
        store = AuthSessionStore()
        request.app.state.auth_sessions = store
    return store


def _persist_session(
    request: Request,
    user: dict[str, Any],
    pair: dict[str, Any],
    session_id: str,
    user_agent: str | None,
    previous: dict[str, Any] | None = None,
) -> None:
    refresh_claims = tokens.peek(pair["refresh_token"]) or {}
    access_claims = tokens.verify_access(pair["access_token"]) or {}
    now = int(time.time())
    payload: dict[str, Any] = {
        "session_id": session_id,
        "user_id": user["id"],
        "username": user.get("username"),
        "role": user.get("role"),
        "permissions": user.get("permissions", []),
        "access_jti": access_claims.get("jti"),
        "refresh_jti": refresh_claims.get("jti"),
        "user_agent": user_agent,
        "created_at": (previous or {}).get("created_at") or now,
        "updated_at": now,
    }
    _session_store(request).save(str(user["id"]), session_id, payload, tokens.REFRESH_TTL)


def _login_with_password(body: LoginRequest) -> dict[str, Any]:
    if not body.username or not body.password:
        raise HTTPException(status_code=400, detail="Both username and password are required")
    database_url = get_database_url()
    if not database_url:
        raise HTTPException(status_code=503, detail="Password login requires TASKER_DATABASE_URL")
    try:
        record = authenticate_user(database_url, body.username, body.password)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Auth store unavailable") from exc
    if record is None:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    user = _user_payload(
        str(record["id"]),
        _permissions_for_db_role(record.get("role")),
        username=str(record["username"]),
    )
    if record.get("email"):
        user["email"] = record["email"]
    return user


def _login_with_api_key(api_key: str, request: Request) -> dict[str, Any]:
    # Wizard master key (notas.md #3): the apiKey shown by the setup wizard
    # (and stored in the secrets store) starts a full admin session so the
    # admin can see the onboarding notifications without a second credential.
    from socialseed_tasker.infrastructure.web_api.routers.setup import (
        MASTER_KEY_PREFIX,
        resolve_master_key,
    )

    if api_key.startswith(MASTER_KEY_PREFIX):
        master_key, admin_username = resolve_master_key(request.app.state)
        if master_key is not None and secrets.compare_digest(api_key, master_key):
            username = admin_username or "admin"
            return _user_payload(
                username, _permissions_for_db_role("admin"), username=username
            )
    provider = load_auth_provider()
    user_id = provider.verify_token(api_key)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    info = provider.get_user_info(user_id) or {}
    permissions = list(info.get("permissions") or _DEFAULT_VIEWER_PERMISSIONS)
    return _user_payload(user_id, permissions, username=info.get("username", user_id))


def _authenticate(body: LoginRequest, request: Request) -> dict[str, Any]:
    if body.username is not None or body.password is not None:
        return _login_with_password(body)
    if body.api_key:
        return _login_with_api_key(body.api_key, request)
    raise HTTPException(status_code=400, detail="Provide username/password or api_key")


def _sweep() -> None:
    now = time.time()
    for store in (_OAUTH_STATES, _EXCHANGE_CODES):
        for key in [k for k, v in store.items() if now - v["created_at"] > max(OAUTH_STATE_TTL, EXCHANGE_CODE_TTL)]:
            store.pop(key, None)


@auth_router.post("/auth/login", summary="Exchange credentials for a JWT session")
def login(
    body: LoginRequest,
    request: Request,
    user_agent: str | None = Header(default=None),
) -> dict[str, Any]:
    user = _authenticate(body, request)
    session_id = uuid.uuid4().hex
    pair = tokens.issue_tokens(user, session_id)
    _persist_session(request, user, pair, session_id, user_agent)
    return _public_session(pair, user)


@auth_router.post("/auth/refresh", summary="Rotate the refresh token")
def refresh(
    body: RefreshRequest,
    request: Request,
    user_agent: str | None = Header(default=None),
) -> dict[str, Any]:
    claims = tokens.peek(body.refresh_token)
    if claims is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    sub = str(claims.get("sub", ""))
    old_session_id = str(claims.get("sid")) if claims.get("sid") else None
    previous: dict[str, Any] | None = None
    if old_session_id:
        previous = _session_store(request).get(sub, old_session_id)
        if previous is None:
            raise HTTPException(status_code=401, detail="Session revoked")
    session_id = old_session_id or uuid.uuid4().hex
    pair = tokens.rotate(body.refresh_token, session_id=session_id)
    if pair is None:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    user = _user_payload(sub, list(claims.get("permissions") or []), username=claims.get("username"))
    _persist_session(request, user, pair, session_id, user_agent, previous=previous)
    return _public_session(pair, user)


@auth_router.post("/auth/logout", summary="Revoke the session and refresh token")
def logout(
    body: LogoutRequest,
    request: Request,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    if body.refresh_token:
        claims = tokens.peek(body.refresh_token)
        tokens.revoke(body.refresh_token)
        if claims is not None and claims.get("sid"):
            _session_store(request).delete(str(claims.get("sub", "")), str(claims["sid"]))
            return {"ok": True}
    if authorization and authorization.startswith("Bearer "):
        access = tokens.verify_access(authorization[7:])
        if access is not None and access.get("sid"):
            _session_store(request).delete(str(access.get("sub", "")), str(access["sid"]))
    return {"ok": True}


@auth_router.get("/auth/me", summary="Current session user")
def me(request: Request, authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    claims = tokens.verify_access(authorization[7:])
    if claims is None:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")
    session_id = claims.get("sid")
    if session_id and _session_store(request).get(str(claims.get("sub", "")), str(session_id)) is None:
        raise HTTPException(status_code=401, detail="Session revoked")
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
def exchange(body: ExchangeRequest, request: Request, user_agent: str | None = Header(default=None)) -> dict[str, Any]:
    _sweep()
    entry = _EXCHANGE_CODES.pop(body.code, None)
    if entry is None:
        raise HTTPException(status_code=401, detail="Invalid or expired authorization code")
    user = entry["user"]
    session_id = uuid.uuid4().hex
    pair = tokens.issue_tokens(user, session_id)
    _persist_session(request, user, pair, session_id, user_agent)
    return _public_session(pair, user)
