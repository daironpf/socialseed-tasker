from __future__ import annotations
import os
from typing import Optional
from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.application.exceptions import StorageError
from socialseed_tasker.observability.tracing import get_tracer

_tracer = get_tracer("tasker.redis_storage")

try:
    import redis  # type: ignore
    _REDIS_AVAILABLE = True
except Exception:
    _REDIS_AVAILABLE = False

class RedisStorage(StoragePort):
    def __init__(self, url: Optional[str] = None) -> None:
        if not _REDIS_AVAILABLE:
            raise StorageError("redis package not available")
        self._url = url or os.getenv("TASKER_REDIS_URL", "redis://localhost:6379/0")
        try:
            self._client = redis.from_url(self._url)
            self._client.ping()
        except Exception as exc:
            raise StorageError(f"Failed to connect to Redis at {self._url}: {exc}") from exc

    def put(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
        with _tracer.start_as_current_span("redis.put"):
            try:
                if ttl_seconds is None:
                    self._client.set(key, value)
                else:
                    self._client.setex(key, ttl_seconds, value)
            except Exception as exc:
                raise StorageError(f"Redis put failed for key {key}: {exc}") from exc

    def get(self, key: str) -> Optional[bytes]:
        with _tracer.start_as_current_span("redis.get"):
            try:
                v = self._client.get(key)
                return v if v is not None else None
            except Exception as exc:
                raise StorageError(f"Redis get failed for key {key}: {exc}") from exc

    def delete(self, key: str) -> None:
        with _tracer.start_as_current_span("redis.delete"):
            try:
                self._client.delete(key)
            except Exception as exc:
                raise StorageError(f"Redis delete failed for key {key}: {exc}") from exc
