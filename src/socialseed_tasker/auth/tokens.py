"""Stateless HS256 JWTs with rotating refresh tokens (issue #519).

Stdlib-only implementation (no new dependencies):

- Access token: short-lived (default 900s), carries user id/role/permissions.
- Refresh token: long-lived (default 604800s), carries a ``jti`` tracked in an
  in-process active set. Rotation discards the old ``jti`` and registers the
  new one; presenting an already-rotated (reused) refresh token revokes every
  active refresh token for that user (reuse detection).
- Both tokens optionally carry ``sid``, the session id of the Redis session
  registry (issue #527). Logout deletes the session key and the auth
  middleware rejects access tokens whose session no longer exists.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from typing import Any

SECRET = os.getenv("TASKER_JWT_SECRET", "tasker-dev-secret-change-me")
ACCESS_TTL = int(os.getenv("TASKER_JWT_ACCESS_TTL", "900"))
REFRESH_TTL = int(os.getenv("TASKER_JWT_REFRESH_TTL", "604800"))


def _b64e(raw: bytes) -> bytes:
    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def _b64d(seg: bytes) -> bytes:
    pad = b"=" * (-len(seg) % 4)
    return base64.urlsafe_b64decode(seg + pad)


def _sign(payload: dict[str, Any]) -> str:
    header = _b64e(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    body = _b64e(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = header + b"." + body
    sig = _b64e(hmac.new(SECRET.encode(), signing_input, hashlib.sha256).digest())
    return (signing_input + b"." + sig).decode()


def _decode(token: str) -> dict[str, Any] | None:
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        signing_input = f"{parts[0]}.{parts[1]}".encode()
        expected = _b64e(hmac.new(SECRET.encode(), signing_input, hashlib.sha256).digest())
        if not hmac.compare_digest(expected, parts[2].encode()):
            return None
        claims: dict[str, Any] = json.loads(_b64d(parts[1].encode()))
        if int(claims.get("exp", 0)) < time.time():
            return None
        return claims
    except Exception:
        return None


# Active refresh jtis per subject. Removal == revocation.
_ACTIVE: dict[str, set[str]] = {}


def _access_claims(user: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
    now = int(time.time())
    claims = {
        "sub": user["id"],
        "username": user.get("username", user["id"]),
        "role": user.get("role", "DEVELOPER"),
        "permissions": user.get("permissions", []),
        "typ": "access",
        "iat": now,
        "exp": now + ACCESS_TTL,
        "jti": uuid.uuid4().hex,
    }
    if session_id:
        claims["sid"] = session_id
    return claims


def issue_tokens(user: dict[str, Any], session_id: str | None = None) -> dict[str, Any]:
    access = _sign(_access_claims(user, session_id))
    now = int(time.time())
    refresh_claims: dict[str, Any] = {
        "sub": user["id"],
        "username": user.get("username", user["id"]),
        "role": user.get("role", "DEVELOPER"),
        "permissions": user.get("permissions", []),
        "typ": "refresh",
        "iat": now,
        "exp": now + REFRESH_TTL,
        "jti": uuid.uuid4().hex,
    }
    if session_id:
        refresh_claims["sid"] = session_id
    refresh = _sign(refresh_claims)
    _ACTIVE.setdefault(refresh_claims["sub"], set()).add(refresh_claims["jti"])
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "expires_in": ACCESS_TTL,
    }


def verify_access(token: str) -> dict[str, Any] | None:
    claims = _decode(token)
    if claims is None or claims.get("typ") != "access":
        return None
    return claims


def verify_refresh(token: str) -> dict[str, Any] | None:
    claims = _decode(token)
    if claims is None or claims.get("typ") != "refresh":
        return None
    jti = str(claims.get("jti", ""))
    sub = str(claims.get("sub", ""))
    active = _ACTIVE.get(sub, set())
    if jti in active:
        return claims
    # Reuse of an already-rotated/revoked refresh token: kill every token
    # belonging to this subject and force a fresh login.
    _ACTIVE.pop(sub, None)
    return None


def rotate(refresh_token: str, session_id: str | None = None) -> dict[str, Any] | None:
    claims = verify_refresh(refresh_token)
    if claims is None:
        # verify_refresh already revoked the subject on reuse; fail closed.
        return None
    active = _ACTIVE.setdefault(claims["sub"], set())
    active.discard(claims.get("jti"))
    user = {
        "id": claims["sub"],
        "username": claims.get("username", claims["sub"]),
        "role": claims.get("role", "DEVELOPER"),
        "permissions": claims.get("permissions", []),
    }
    return issue_tokens(user, session_id=session_id or claims.get("sid"))


def revoke(refresh_token: str) -> None:
    claims = _decode(refresh_token)
    if claims is None or claims.get("typ") != "refresh":
        return
    _ACTIVE.get(claims.get("sub", ""), set()).discard(claims.get("jti"))


def peek(refresh_token: str) -> dict[str, Any] | None:
    """Validate signature/expiry of a refresh token without touching the active set."""
    claims = _decode(refresh_token)
    if claims is None or claims.get("typ") != "refresh":
        return None
    return claims
