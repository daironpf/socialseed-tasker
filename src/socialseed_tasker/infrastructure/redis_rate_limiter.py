from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

try:
    import redis  # type: ignore
    _REDIS_AVAILABLE = True
except Exception:
    _REDIS_AVAILABLE = False

LUA_SCRIPT = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local capacity = tonumber(ARGV[3])
local tokens_needed = tonumber(ARGV[4])
local data = redis.call("HMGET", key, "tokens", "last_ts")
local tokens = tonumber(data[1]) or capacity
local last_ts = tonumber(data[2]) or now
local elapsed = math.max(0, now - last_ts)
tokens = math.min(capacity, tokens + elapsed * rate)
if tokens >= tokens_needed then
  tokens = tokens - tokens_needed
  redis.call("HMSET", key, "tokens", tokens, "last_ts", now)
  redis.call("EXPIRE", key, 3600)
  return {1, tokens}
else
  redis.call("HMSET", key, "tokens", tokens, "last_ts", now)
  redis.call("EXPIRE", key, 3600)
  return {0, tokens}
end
"""


class RedisRateLimiter:
    def __init__(self, redis_url: Optional[str] = None, rate_per_min: int = 60, burst: int = 20):
        if not _REDIS_AVAILABLE:
            raise RuntimeError("redis package not available")
        self._url = redis_url or os.getenv("TASKER_REDIS_URL", "redis://localhost:6379/0")
        self._client = redis.from_url(self._url)
        self.rate_per_min = rate_per_min
        self.burst = burst
        self._script = self._client.register_script(LUA_SCRIPT)

    def allow(self, key: str, tokens: int = 1) -> bool:
        now = time.time()
        rate = float(self.rate_per_min) / 60.0
        capacity = float(self.burst)
        res = self._script(keys=[f"ratelimit:{key}"], args=[now, rate, capacity, tokens])
        allowed = bool(res[0])
        return allowed

    def get_state(self, key: str) -> Dict[str, Any]:
        data = self._client.hgetall(f"ratelimit:{key}")
        tokens = float(data.get(b"tokens", b"0")) if data else 0.0
        last_ts = float(data.get(b"last_ts", b"0")) if data else 0.0
        return {"tokens": tokens, "last_ts": last_ts, "rate_per_min": self.rate_per_min, "burst": self.burst}

    def reset(self, key: str) -> None:
        self._client.delete(f"ratelimit:{key}")
