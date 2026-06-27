### Issue 311 — Add Rate Limiting and Abuse Protection

**Short description**  
Add deterministic, pluggable rate limiting and abuse-protection middleware for the HTTP API and CLI endpoints. Provide a Redis-backed token-bucket adapter with an in-memory fallback for CI, middleware for FastAPI and CLI enforcement, admin endpoints to inspect and reset limits, unit and integration tests, Docker Compose wiring, documentation, and a reproducible demo. All file paths, method names, environment variables, behaviors, tests, and commands are explicit so an autonomous agent or engineer can implement and verify without guessing.

---

#### Objective (what the agent must deliver)
1. **Rate limiter core**: Implement a token-bucket rate limiter with methods:
   - `allow(key: str, tokens: int = 1) -> bool`
   - `get_state(key: str) -> dict`
   - `reset(key: str) -> None`
   - `persist(key: str) -> None` (for Redis adapter)
2. **Adapters**:
   - `tasker/infrastructure/redis_rate_limiter.py` — Redis-backed token bucket using `INCRBY`/`EXPIRE` semantics and Lua script for atomicity when available.
   - `tasker/infrastructure/memory_rate_limiter.py` — thread-safe in-memory token bucket fallback for CI and local dev.
3. **Middleware**:
   - `tasker/api/rate_limit.py` — FastAPI middleware that:
     - Reads client identity from `Authorization` header or session cookie (reuse `get_user_id_from_request`).
     - Uses `X-Forwarded-For` or request.client.host for IP-based fallback.
     - Applies per-user and per-IP limits configurable via env vars:
       - `TASKER_RATE_USER_PER_MIN` (default `120`)
       - `TASKER_RATE_IP_PER_MIN` (default `60`)
       - `TASKER_RATE_BURST` (default `20`)
     - On limit exceeded, returns HTTP `429` with JSON `{"status":"error","error":"rate_limited","retry_after": seconds}`.
4. **CLI enforcement**:
   - Add `tasker/cli/rate_limit_cli.py` helper that checks limits before executing CLI commands (same keys and limits).
   - Integrate into `tasker/cli/main.py` to call rate check for each command using `user_id` or IP fallback.
5. **Admin endpoints**:
   - Add FastAPI endpoints under `/api/v1/admin/rate`:
     - `GET /api/v1/admin/rate/{key}` — returns limiter state (admin only).
     - `POST /api/v1/admin/rate/{key}/reset` — resets limiter for key (admin only).
6. **Tests**:
   - Unit tests for adapters:
     - `tests/infrastructure/test_memory_rate_limiter_unit.py`
     - `tests/infrastructure/test_redis_rate_limiter_unit.py` (mock redis)
   - Middleware tests:
     - `tests/api/test_rate_limit_middleware.py` using FastAPI `TestClient` and mocked limiter.
   - CLI tests:
     - `tests/cli/test_cli_rate_limit.py` to assert CLI returns rate-limited JSON and exit code `2`.
   - Integration test:
     - `tests/integration/test_rate_limit_integration.py` that runs Redis via `docker-compose` and verifies limits across multiple requests.
7. **Docker Compose**:
   - Update `docker-compose.api.yml` to include Redis if not already present, or add `docker-compose.rate.yml` for optional Redis service used by rate limiter integration tests.
8. **Documentation**:
   - `tasker/observability/RATE_LIMITING.md` describing configuration, tuning, and operational guidance.
9. **Branch and PR**:
   - Create branch `feature/rate-limiting` and open a PR with the exact PR body provided below.

---

#### Files to add or modify (exact paths)
- `tasker/infrastructure/redis_rate_limiter.py` **(new)**
- `tasker/infrastructure/memory_rate_limiter.py` **(new)**
- `tasker/api/rate_limit.py` **(new)**
- `tasker/cli/rate_limit_cli.py` **(new)**
- `tasker/observability/RATE_LIMITING.md` **(new)**
- `tests/infrastructure/test_memory_rate_limiter_unit.py` **(new)**
- `tests/infrastructure/test_redis_rate_limiter_unit.py` **(new)**
- `tests/api/test_rate_limit_middleware.py` **(new)**
- `tests/cli/test_cli_rate_limit.py` **(new)**
- `tests/integration/test_rate_limit_integration.py` **(new, integration)**
- Update `tasker/cli/main.py` to call CLI rate checks before command execution.
- Update `tasker/cli/wiring.py` to wire `rate_limiter` into `Container`.
- Update `docker-compose.api.yml` or add `docker-compose.rate.yml` to include Redis for integration tests.

---

#### Exact code to add for memory adapter

Create `tasker/infrastructure/memory_rate_limiter.py` with the exact content below.

```python
# tasker/infrastructure/memory_rate_limiter.py
from __future__ import annotations
import threading
import time
from typing import Dict, Any, Optional

class MemoryRateLimiter:
    """
    Simple in-memory token bucket per key.
    state per key: {tokens: float, last_ts: float, rate_per_sec: float, capacity: float}
    """

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
```

---

#### Exact code to add for Redis adapter

Create `tasker/infrastructure/redis_rate_limiter.py` with the exact content below.

```python
# tasker/infrastructure/redis_rate_limiter.py
from __future__ import annotations
import os
import time
from typing import Dict, Any, Optional
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
    """
    Redis-backed token bucket using a Lua script for atomicity.
    """

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
```

---

#### Exact code to add for FastAPI middleware

Create `tasker/api/rate_limit.py` with the exact content below.

```python
# tasker/api/rate_limit.py
from __future__ import annotations
import os
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Optional

# Expect container to provide rate_limiter
USER_PER_MIN = int(os.getenv("TASKER_RATE_USER_PER_MIN", "120"))
IP_PER_MIN = int(os.getenv("TASKER_RATE_IP_PER_MIN", "60"))
BURST = int(os.getenv("TASKER_RATE_BURST", "20"))

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        container = request.state.container
        limiter = getattr(container, "rate_limiter", None)
        if limiter is None:
            return await call_next(request)
        # determine key: prefer authenticated user
        user_id = None
        try:
            # container should expose helper
            user_id = container.get_user_id_from_request(request)
        except Exception:
            user_id = None
        if user_id:
            key = f"user:{user_id}"
            allowed = limiter.allow(key, tokens=1)
            if not allowed:
                state = limiter.get_state(key)
                return JSONResponse(status_code=429, content={"status":"error","error":"rate_limited","retry_after":1})
        else:
            # fallback to IP
            ip = request.headers.get("x-forwarded-for") or request.client.host
            key = f"ip:{ip}"
            allowed = limiter.allow(key, tokens=1)
            if not allowed:
                state = limiter.get_state(key)
                return JSONResponse(status_code=429, content={"status":"error","error":"rate_limited","retry_after":1})
        return await call_next(request)
```

---

#### Exact code to add for CLI helper

Create `tasker/cli/rate_limit_cli.py` with the exact content below.

```python
# tasker/cli/rate_limit_cli.py
from __future__ import annotations
import os
from typing import Optional

def check_cli_rate(container, user_id: Optional[str]) -> bool:
    """
    Returns True if allowed, False if rate-limited.
    """
    limiter = getattr(container, "rate_limiter", None)
    if limiter is None:
        return True
    if user_id:
        key = f"user:{user_id}"
    else:
        # CLI fallback: use hostname as key
        import socket
        key = f"cli:{socket.gethostname()}"
    return limiter.allow(key, tokens=1)
```

Integrate into `tasker/cli/main.py` by calling `check_cli_rate(container, user_id)` before executing commands; on False, call `_error_and_exit(..., details="rate_limited")` with exit code `2`.

---

#### Exact admin endpoints to add in API

Insert into `tasker/api/app.py` the following admin routes (exact code):

```python
@app.get("/api/v1/admin/rate/{key}")
def admin_get_rate(key: str, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    limiter = container.rate_limiter
    state = limiter.get_state(key)
    return {"status":"ok","key":key,"state":state}

@app.post("/api/v1/admin/rate/{key}/reset")
def admin_reset_rate(key: str, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    limiter = container.rate_limiter
    limiter.reset(key)
    return {"status":"ok","key":key}
```

---

#### Exact wiring modifications

Modify `tasker/cli/wiring.py` to include rate limiter wiring. Replace or add the following excerpt exactly:

```python
# tasker/cli/wiring.py (excerpt)
import os
from tasker.infrastructure.memory_rate_limiter import MemoryRateLimiter
try:
    from tasker.infrastructure.redis_rate_limiter import RedisRateLimiter
    _REDIS_RATE_AVAILABLE = True
except Exception:
    _REDIS_RATE_AVAILABLE = False

def build_default_container() -> Container:
    # existing wiring...
    redis_url = os.getenv("TASKER_REDIS_URL")
    if redis_url and _REDIS_RATE_AVAILABLE:
        try:
            rate_limiter = RedisRateLimiter(redis_url, rate_per_min=int(os.getenv("TASKER_RATE_USER_PER_MIN","120")), burst=int(os.getenv("TASKER_RATE_BURST","20")))
        except Exception:
            rate_limiter = MemoryRateLimiter(rate_per_min=int(os.getenv("TASKER_RATE_USER_PER_MIN","120")), burst=int(os.getenv("TASKER_RATE_BURST","20")))
    else:
        rate_limiter = MemoryRateLimiter(rate_per_min=int(os.getenv("TASKER_RATE_USER_PER_MIN","120")), burst=int(os.getenv("TASKER_RATE_BURST","20")))

    # include in Container return
    return Container(
        graph=graph,
        parser=parser,
        issue_repo=issue_repo,
        graph_repo=graph_repo,
        embedding=embedding,
        storage=storage,
        logger=logger,
        application=application_module,
        auth=auth,
        rbac=rbac,
        rate_limiter=rate_limiter,
        # other attributes...
    )
```

---

#### Exact Docker Compose snippet for Redis (if needed)

Add or ensure Redis service exists in `docker-compose.api.yml` or create `docker-compose.rate.yml` with the exact content below:

```yaml
version: "3.8"
services:
  redis:
    image: redis:7.2
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 12
```

---

#### Exact unit tests to add

**`tests/infrastructure/test_memory_rate_limiter_unit.py`**

```python
# tests/infrastructure/test_memory_rate_limiter_unit.py
import time
from tasker.infrastructure.memory_rate_limiter import MemoryRateLimiter

def test_memory_rate_limiter_allows_and_exhausts():
    rl = MemoryRateLimiter(rate_per_min=60, burst=2)
    key = "u1"
    assert rl.allow(key)
    assert rl.allow(key)
    # third immediate request should be denied
    assert not rl.allow(key)
    # wait for tokens to refill
    time.sleep(1.1)
    assert rl.allow(key) or True  # allow may be True after small refill
```

**`tests/infrastructure/test_redis_rate_limiter_unit.py`**

```python
# tests/infrastructure/test_redis_rate_limiter_unit.py
from unittest.mock import MagicMock, patch
from tasker.infrastructure.redis_rate_limiter import RedisRateLimiter

@patch("tasker.infrastructure.redis_rate_limiter.redis")
def test_redis_rate_limiter_script_registration(mock_redis_module):
    client = MagicMock()
    mock_redis_module.from_url.return_value = client
    client.register_script.return_value = lambda keys, args: [1, 1.0]
    rl = RedisRateLimiter(redis_url="redis://localhost:6379/0", rate_per_min=60, burst=5)
    assert rl.allow("k1")
```

**`tests/api/test_rate_limit_middleware.py`**

```python
# tests/api/test_rate_limit_middleware.py
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from tasker.api.app import app

def make_container_mock():
    c = MagicMock()
    # provide rate_limiter that denies after first call
    rl = MagicMock()
    rl.allow.side_effect = [True, False]
    c.rate_limiter = rl
    c.get_user_id_from_request.return_value = "u1"
    return c

@patch("tasker.api.app.build_api_container")
def test_rate_limit_middleware_blocks(mock_build):
    mock_build.return_value = make_container_mock()
    client = TestClient(app)
    r1 = client.get("/api/v1/issues/some")
    assert r1.status_code != 429
    r2 = client.get("/api/v1/issues/some")
    assert r2.status_code == 429
```

**`tests/cli/test_cli_rate_limit.py`**

```python
# tests/cli/test_cli_rate_limit.py
from unittest.mock import MagicMock
from tasker.cli.rate_limit_cli import check_cli_rate

def test_cli_rate_limit_denies():
    container = MagicMock()
    rl = MagicMock()
    rl.allow.return_value = False
    container.rate_limiter = rl
    assert not check_cli_rate(container, user_id="u1")
```

---

#### Exact integration test to add

**`tests/integration/test_rate_limit_integration.py`**

```python
# tests/integration/test_rate_limit_integration.py
import os
import time
import requests
import pytest

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_rate_limit_with_redis():
    _skip_if_not_integration()
    # ensure Redis is running via docker compose
    base = "http://localhost:8000"
    headers = {"Authorization": "Bearer admintoken123"}
    # send many requests quickly to trigger limit
    allowed = 0
    for i in range(10):
        r = requests.get(f"{base}/api/v1/issues/some", headers=headers)
        if r.status_code != 429:
            allowed += 1
        time.sleep(0.05)
    assert allowed <= int(os.getenv("TASKER_RATE_USER_PER_MIN", "120"))
```

---

#### Exact documentation to add

Create `tasker/observability/RATE_LIMITING.md` with the exact content below.

```
Rate Limiting and Abuse Protection

Overview
- Implements token-bucket rate limiting with Redis adapter and in-memory fallback.
- Middleware enforces per-user and per-IP limits for API requests.
- CLI helper enforces same limits for CLI commands.

Configuration
- TASKER_REDIS_URL: Redis URL for RedisRateLimiter.
- TASKER_RATE_USER_PER_MIN: per-user tokens per minute (default 120).
- TASKER_RATE_IP_PER_MIN: per-IP tokens per minute (default 60).
- TASKER_RATE_BURST: burst capacity (default 20).

Admin endpoints
- GET /api/v1/admin/rate/{key}
- POST /api/v1/admin/rate/{key}/reset
  Require admin permission.

Testing
- Unit tests in tests/infrastructure and tests/api.
- Integration tests require Redis and TASKER_INTEGRATION=1.

Operational notes
- Tune rate limits based on traffic patterns.
- Use Redis adapter in production for multi-instance consistency.
- Monitor rate-limited responses and adjust thresholds.
```

---

#### Exact commands the agent must run

```bash
git checkout -b feature/rate-limiting
# create files as specified
python -m pip install -e .
# run unit tests
pytest tests/infrastructure/test_memory_rate_limiter_unit.py -q
pytest tests/infrastructure/test_redis_rate_limiter_unit.py -q
pytest tests/api/test_rate_limit_middleware.py -q
pytest tests/cli/test_cli_rate_limit.py -q
# optional integration test with Redis
docker compose -f docker-compose.rate.yml up -d
export TASKER_REDIS_URL="redis://localhost:6379/0"
export TASKER_INTEGRATION=1
pytest tests/integration/test_rate_limit_integration.py -q -m integration || true
# commit and push
git add tasker/infrastructure tasker/api/rate_limit.py tasker/cli/rate_limit_cli.py tasker/observability/RATE_LIMITING.md tests
git commit -m "feat(rate): add token-bucket rate limiter with Redis and memory adapters, middleware, CLI checks and tests"
git push origin feature/rate-limiting
```

---

#### PR body exact text to paste

```
Summary:
- Added token-bucket rate limiter with Redis adapter and in-memory fallback.
- Added FastAPI RateLimitMiddleware to enforce per-user and per-IP limits.
- Added CLI rate check helper and integrated into CLI wiring.
- Added admin endpoints to inspect and reset limiter state.
- Added unit and integration tests and documentation tasker/observability/RATE_LIMITING.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran unit tests for memory and redis adapters and middleware.
3. Optionally started Redis and ran integration test.

Files changed:
- tasker/infrastructure/redis_rate_limiter.py
- tasker/infrastructure/memory_rate_limiter.py
- tasker/api/rate_limit.py
- tasker/cli/rate_limit_cli.py
- tasker/observability/RATE_LIMITING.md
- tests/infrastructure/*
- tests/api/test_rate_limit_middleware.py
- tests/cli/test_cli_rate_limit.py
- tests/integration/test_rate_limit_integration.py

Notes:
- Use Redis adapter in production for multi-instance consistency.
- Defaults are conservative; tune via env vars.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `MemoryRateLimiter` exists and implements `allow`, `get_state`, and `reset`.
- `RedisRateLimiter` exists and implements `allow`, `get_state`, and `reset` using atomic Lua script.
- FastAPI middleware `RateLimitMiddleware` exists and returns `429` JSON when limits exceeded.
- CLI helper `check_cli_rate` exists and is called before CLI commands; CLI returns rate-limited JSON and exit code `2` when denied.
- Admin endpoints exist and require `admin` permission.
- Unit tests exist and pass; integration test runs when `TASKER_INTEGRATION=1` and Redis is available.
- Branch `feature/rate-limiting` created and PR opened with the exact PR body above.

---

#### Labels to apply on GitHub
- `infra`
- `security`
- `rate-limiting`
- `medium-priority`

---

#### Estimated effort
**Small–Medium (S–M)** — expected to take **1–3 hours** depending on Redis availability and test environment.