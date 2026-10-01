"""Shared storage configuration — TASKER_DATABASE_URL / TASKER_REDIS_URL with in-memory fallback."""

from __future__ import annotations

import os

from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.infrastructure.redis_storage import RedisStorage


def get_redis_url() -> str | None:
    """Return TASKER_REDIS_URL when configured, else None (in-process fallback)."""
    return os.getenv("TASKER_REDIS_URL") or None


def get_database_url() -> str | None:
    """Return TASKER_DATABASE_URL when configured, else None."""
    return os.getenv("TASKER_DATABASE_URL") or None


def get_mongo_url() -> str | None:
    """Return TASKER_MONGO_URL when configured, else None (chat persistence disabled)."""
    return os.getenv("TASKER_MONGO_URL") or None


def build_storage() -> tuple[str, StoragePort]:
    """Return (backend_name, storage): Redis when TASKER_REDIS_URL is set and reachable, memory otherwise."""
    redis_url = get_redis_url()
    if redis_url:
        try:
            return "redis", RedisStorage(url=redis_url)  # type: ignore[abstract]
        except Exception:
            pass
    return "memory", MemoryStorage()
