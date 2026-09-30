"""Redis-backed session registry for JWT logins with an in-memory fallback (issue #527).

Sessions live under ``session:{user_id}:{session_id}`` with a TTL equal to the
refresh-token lifetime. ``POST /auth/logout`` deletes the key and the auth
middleware rejects access tokens whose session is gone. Without
``TASKER_REDIS_URL`` (or when Redis is unreachable) the store degrades to an
in-process dictionary so local development keeps working.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any

logger = logging.getLogger(__name__)

SESSION_PREFIX = "session"


def session_key(user_id: str, session_id: str) -> str:
    """Build the registry key ``session:{user_id}:{session_id}``."""
    return f"{SESSION_PREFIX}:{user_id}:{session_id}"


class AuthSessionStore:
    """Persist auth sessions in Redis, falling back to an in-process dict."""

    def __init__(self, redis_url: str | None = None) -> None:
        self._url = redis_url if redis_url is not None else (os.getenv("TASKER_REDIS_URL") or None)
        self._client: Any = None
        self._memory: dict[str, tuple[dict[str, Any], float]] = {}
        self._lock = threading.Lock()
        if self._url:
            try:
                import redis

                client = redis.from_url(self._url, decode_responses=True)
                client.ping()
                self._client = client
            except Exception as exc:
                logger.warning("redis session store unavailable (%s); using in-memory fallback", exc)

    @property
    def backend(self) -> str:
        return "redis" if self._client is not None else "memory"

    def save(self, user_id: str, session_id: str, payload: dict[str, Any], ttl: int) -> None:
        """Store a session payload under its key, expiring after ``ttl`` seconds."""
        key = session_key(user_id, session_id)
        if self._client is not None:
            try:
                self._client.setex(key, ttl, json.dumps(payload))
                return
            except Exception as exc:
                self._degrade("save", exc)
        self._memory_save(key, payload, ttl)

    def get(self, user_id: str, session_id: str) -> dict[str, Any] | None:
        """Return the session payload, or None when missing or expired."""
        key = session_key(user_id, session_id)
        if self._client is not None:
            try:
                raw = self._client.get(key)
                return json.loads(raw) if raw else None
            except Exception as exc:
                self._degrade("get", exc)
        return self._memory_get(key)

    def delete(self, user_id: str, session_id: str) -> None:
        """Revoke a session by removing its key (logout)."""
        key = session_key(user_id, session_id)
        if self._client is not None:
            try:
                self._client.delete(key)
                return
            except Exception as exc:
                self._degrade("delete", exc)
        self._memory_delete(key)

    def _degrade(self, operation: str, exc: Exception) -> None:
        logger.warning("redis session %s failed (%s); degrading to in-memory store", operation, exc)
        self._client = None

    def _memory_save(self, key: str, payload: dict[str, Any], ttl: int) -> None:
        now = time.time()
        with self._lock:
            self._sweep(now)
            self._memory[key] = (dict(payload), now + ttl)

    def _memory_get(self, key: str) -> dict[str, Any] | None:
        now = time.time()
        with self._lock:
            entry = self._memory.get(key)
            if entry is None:
                return None
            payload, expires_at = entry
            if expires_at <= now:
                self._memory.pop(key, None)
                return None
            return dict(payload)

    def _memory_delete(self, key: str) -> None:
        with self._lock:
            self._memory.pop(key, None)

    def _sweep(self, now: float) -> None:
        expired = [key for key, (_, expires_at) in self._memory.items() if expires_at <= now]
        for key in expired:
            self._memory.pop(key, None)
