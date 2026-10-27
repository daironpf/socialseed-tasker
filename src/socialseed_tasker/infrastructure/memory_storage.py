from __future__ import annotations

import threading
import time

from socialseed_tasker.application.ports import StoragePort
from socialseed_tasker.observability.tracing import get_tracer


def _get_tracer():
    return get_tracer("tasker.memory_storage")

class MemoryStorage(StoragePort):
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: dict[str, tuple[bytes, float | None]] = {}

    def put(self, key: str, value: bytes, ttl_seconds: int | None = None) -> None:
        with _get_tracer().start_as_current_span("memory.put"):
            expire = None
            if ttl_seconds is not None:
                expire = time.time() + float(ttl_seconds)
            with self._lock:
                self._store[key] = (value, expire)

    def get(self, key: str) -> bytes | None:
        with _get_tracer().start_as_current_span("memory.get"), self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            value, expire = item
            if expire is not None and time.time() > expire:
                del self._store[key]
                return None
            return value

    def delete(self, key: str) -> None:
        with _get_tracer().start_as_current_span("memory.delete"), self._lock:
            self._store.pop(key, None)

    def list_keys(self) -> list[str]:
        with self._lock:
            return list(self._store.keys())
