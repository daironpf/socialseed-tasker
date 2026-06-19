from __future__ import annotations

import os

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

USER_PER_MIN = int(os.getenv("TASKER_RATE_USER_PER_MIN", "120"))
IP_PER_MIN = int(os.getenv("TASKER_RATE_IP_PER_MIN", "60"))
BURST = int(os.getenv("TASKER_RATE_BURST", "60"))


def _compute_retry_after(limiter, key: str) -> int:
    state = getattr(limiter, "get_state", None)
    if state is None:
        return 1
    try:
        s = state(key)
        tokens = s.get("tokens", 0)
        rate_per_min = s.get("rate_per_min", 60)
        rate_per_sec = rate_per_min / 60.0
        if rate_per_sec <= 0:
            return 1
        wait = (1 - max(0, tokens)) / rate_per_sec
        return max(1, int(wait) + 1)
    except Exception:
        return 1


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        limiter = getattr(request.app.state, "rate_limiter", None)
        if limiter is None:
            return await call_next(request)
        user_id = None
        from socialseed_tasker.auth.oauth import SESSION_COOKIE_NAME
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
            from socialseed_tasker.auth.auth import load_auth_provider
            provider = load_auth_provider()
            user_id = provider.verify_token(token)
        if not user_id:
            sid = request.cookies.get(SESSION_COOKIE_NAME)
            if sid:
                session = getattr(request.app.state, "session_store", None)
                if session:
                    data = session.get(sid)
                    if data:
                        claims = data.get("claims", {})
                        user_id = claims.get("preferred_username") or claims.get("sub")
        if user_id:
            key = f"user:{user_id}"
            allowed = limiter.allow(key, tokens=1)
            if not allowed:
                retry_after = _compute_retry_after(limiter, key)
                return JSONResponse(status_code=429, content={"status": "error", "error": "rate_limited", "retry_after": retry_after}, headers={"Retry-After": str(retry_after)})
        else:
            ip = request.headers.get("x-forwarded-for") or (request.client.host if request.client else "unknown")
            key = f"ip:{ip}"
            allowed = limiter.allow(key, tokens=1)
            if not allowed:
                retry_after = _compute_retry_after(limiter, key)
                return JSONResponse(status_code=429, content={"status": "error", "error": "rate_limited", "retry_after": retry_after}, headers={"Retry-After": str(retry_after)})
        return await call_next(request)
