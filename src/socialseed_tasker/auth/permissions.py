"""Unified permission guard for admin HTTP surfaces (issue #593).

Single policy point shared by ``/admin/tenants`` and ``/data-quality`` writes,
which previously duplicated a broken guard: both resolved identity only via
the static-token auth provider (``TASKER_AUTH_USERS`` / ``auth/users.json``)
and permissions only via the RBAC store granted from ``TASKER_AUTH_USERS`` —
neither ever sees the JWT issued by ``/auth/login``, so every admin got a
systematic 403 when the env var was not defined.

Identity and permission sources, in order:

1. Static bearer token: RBAC store (env grants) or the auth provider's own
   per-user ``permissions`` list (``auth/users.json``).
2. Signed access JWT: its ``role``/``permissions`` claims — derived from the
   same user store at login — decide (same policy app.py already applied to
   ``/admin/flags``).
3. OAuth session cookie: server-side session claims resolved against the
   RBAC store / auth provider.

Everything else is denied with 403; anonymous callers are never trusted.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request


def _forbidden() -> HTTPException:
    return HTTPException(status_code=403, detail="forbidden")


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
        return token or None
    api_key = request.headers.get("x-api-key", "").strip()
    return api_key or None


def _session_user(request: Request) -> str | None:
    from socialseed_tasker.auth.oauth import SESSION_COOKIE_NAME

    sid = request.cookies.get(SESSION_COOKIE_NAME)
    if not sid:
        return None
    session_store = getattr(request.app.state, "session_store", None)
    if not session_store:
        return None
    session = session_store.get(sid)
    if not session:
        return None
    claims = session.get("claims", {})
    if not isinstance(claims, dict):
        return None
    user_id = claims.get("preferred_username") or claims.get("sub")
    return user_id if isinstance(user_id, str) else None


def _granted(container: Any, user_id: str, permission: str) -> bool:
    """RBAC store (TASKER_AUTH_USERS grants) or the auth provider's own list."""
    if container is not None and container.rbac.has_permission(user_id, permission):
        return True
    from socialseed_tasker.auth.auth import load_auth_provider

    info = load_auth_provider().get_user_info(user_id)
    if isinstance(info, dict):
        return permission in (info.get("permissions") or [])
    return False


def require_permission(request: Request, permission: str, container: Any) -> str:
    """Enforce ``permission`` for the caller; return the identity or raise 403."""
    token = _bearer_token(request)
    if token:
        from socialseed_tasker.auth.auth import load_auth_provider

        static_user = load_auth_provider().verify_token(token)
        if static_user:
            if not _granted(container, static_user, permission):
                raise _forbidden()
            return static_user

        from socialseed_tasker.auth.tokens import verify_access

        claims = verify_access(token)
        if claims:
            allowed = permission in (claims.get("permissions") or [])
            if not allowed and permission == "admin" and claims.get("role") == "ADMIN":
                allowed = True
            if not allowed:
                raise _forbidden()
            return str(claims.get("sub") or claims.get("username") or "")

    session_user = _session_user(request)
    if session_user and _granted(container, session_user, permission):
        return session_user
    raise _forbidden()
