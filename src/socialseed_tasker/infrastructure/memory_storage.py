from __future__ import annotations
import threading
import time
from typing import Optional, Dict, Tuple
from socialseed_tasker.application.ports import StoragePort

class MemoryStorage(StoragePort):
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._store: Dict[str, Tuple[bytes, Optional[float]]] = {}

    def put(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
        expire = None
        if ttl_seconds is not None:
            expire = time.time() + float(ttl_seconds)
        with self._lock:
            self._store[key] = (value, expire)

    def get(self, key: str) -> Optional[bytes]:
        with self._lock:
            item = self._store.get(key)
            if item is None:
                return None
            value, expire = item
            if expire is not None and time.time() > expire:
                del self._store[key]
                return None
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
