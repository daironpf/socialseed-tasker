from __future__ import annotations

import threading
import time
from typing import Any, Dict


class MemoryRateLimiter:
    def __init__(self, rate_per_min: int = 60, burst: int = 20):
        self._lock = threading.RLock()
        self._store: Dict[str, Dict[str, Any]] = {}
        self.rate_per_min = rate_per_min
        self.burst = burst

    def _init_key(self, key: str):
        if key not in self._store:
            self._store[key] = {
                "tokens": float(self.burst),
                "last_ts": time.time(),
                "rate_per_sec": float(self.rate_per_min) / 60.0,
                "capacity": float(self.burst),
            }

    def allow(self, key: str, tokens: int = 1) -> bool:
        with self._lock:
            self._init_key(key)
            s = self._store[key]
            now = time.time()
            elapsed = now - s["last_ts"]
            s["tokens"] = min(s["capacity"], s["tokens"] + elapsed * s["rate_per_sec"])
            s["last_ts"] = now
            if s["tokens"] >= tokens:
                s["tokens"] -= tokens
                return True
            return False

    def get_state(self, key: str) -> Dict[str, Any]:
        with self._lock:
            self._init_key(key)
            s = self._store[key].copy()
            return {"tokens": s["tokens"], "last_ts": s["last_ts"], "rate_per_min": self.rate_per_min, "burst": self.burst}

    def reset(self, key: str) -> None:
        with self._lock:
            if key in self._store:
                self._store.pop(key)
