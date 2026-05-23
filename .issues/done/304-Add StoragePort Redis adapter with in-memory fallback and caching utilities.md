### Issue 304 — Add StoragePort Redis adapter with in-memory fallback and caching utilities

**Short description**  
Implement a deterministic `StoragePort` adapter backed by Redis for caching and RAG artifacts, plus a pure in-memory fallback for environments without Redis. Provide helper utilities for common caching patterns (get-or-set, memoize with TTL), unit and integration tests, a Docker Compose Redis service for integration tests, and documentation. All method names, file paths, signatures, tests, commands, and PR text are explicit so an autonomous agent can implement and verify without guessing.

---

#### Objective (what the agent must deliver)
1. Add `tasker/infrastructure/redis_storage.py` implementing `tasker.application.ports.StoragePort` with methods `put`, `get`, and `delete`. Use `redis` Python client when available; otherwise raise `StorageError` on adapter init.
2. Add `tasker/infrastructure/memory_storage.py` implementing `StoragePort` as an in-memory TTL-capable store (thread-safe).
3. Add caching utilities in `tasker/application/cache_utils.py`:
   - `get_or_set(storage: StoragePort, key: str, factory: Callable[[], bytes], ttl_seconds: Optional[int]) -> bytes`
   - `memoize(ttl_seconds: Optional[int] = None)` decorator for functions returning `bytes` or JSON-serializable objects (store serialized bytes).
4. Add unit tests:
   - `tests/infrastructure/test_memory_storage_unit.py`
   - `tests/infrastructure/test_redis_storage_unit.py` (mock redis client)
   - `tests/application/test_cache_utils_unit.py`
5. Add integration test `tests/integration/test_redis_storage_integration.py` that runs only when Redis is available via `docker-compose.redis.yml`.
6. Add `docker-compose.redis.yml` at repo root to start Redis for integration tests.
7. Add documentation `tasker/infrastructure/STORAGE.md` describing adapter behavior, TTL semantics, error mapping to `StorageError`, and examples.
8. Update `tasker/cli/wiring.py` to include `storage` in `Container` using Redis adapter when `TASKER_REDIS_URL` is set, otherwise use memory storage.
9. Create branch `feature/storage-redis-memory` and open a PR with the exact PR body provided below.

---

#### Why this must be done exactly this way
- Agents and application code must rely on a stable `StoragePort` contract for caching and RAG artifacts.
- A Redis-backed adapter provides production-grade persistence; an in-memory fallback ensures deterministic behavior in CI and local dev.
- Utilities `get_or_set` and `memoize` standardize caching patterns and reduce duplication.

---

#### Files to add or modify (exact paths)
- `tasker/infrastructure/redis_storage.py` **(new)**
- `tasker/infrastructure/memory_storage.py` **(new)**
- `tasker/application/cache_utils.py` **(new)**
- `tasker/infrastructure/STORAGE.md` **(new)**
- `docker-compose.redis.yml` **(new at repo root)**
- `tests/infrastructure/test_memory_storage_unit.py` **(new)**
- `tests/infrastructure/test_redis_storage_unit.py` **(new)**
- `tests/application/test_cache_utils_unit.py` **(new)**
- `tests/integration/test_redis_storage_integration.py` **(new, integration)**
- Modify `tasker/cli/wiring.py` to wire `storage` into `Container`.

---

#### Exact code to add for Redis adapter

Create `tasker/infrastructure/redis_storage.py` with the exact content below.

```python
# tasker/infrastructure/redis_storage.py
from __future__ import annotations
import os
from typing import Optional
from tasker.application.ports import StoragePort
from tasker.application.exceptions import StorageError

try:
    import redis  # type: ignore
    _REDIS_AVAILABLE = True
except Exception:
    _REDIS_AVAILABLE = False

class RedisStorage(StoragePort):
    """
    Redis-backed StoragePort implementation.

    Behavior:
    - put stores bytes under key with optional TTL (seconds).
    - get returns bytes or None.
    - delete removes key if exists.
    - Raises StorageError on connection or operation failures.
    """

    def __init__(self, url: Optional[str] = None) -> None:
        if not _REDIS_AVAILABLE:
            raise StorageError("redis package not available")
        self._url = url or os.getenv("TASKER_REDIS_URL", "redis://localhost:6379/0")
        try:
            self._client = redis.from_url(self._url)
            # test connection
            self._client.ping()
        except Exception as exc:
            raise StorageError(f"Failed to connect to Redis at {self._url}: {exc}") from exc

    def put(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
        try:
            if ttl_seconds is None:
                self._client.set(key, value)
            else:
                self._client.setex(key, ttl_seconds, value)
        except Exception as exc:
            raise StorageError(f"Redis put failed for key {key}: {exc}") from exc

    def get(self, key: str) -> Optional[bytes]:
        try:
            v = self._client.get(key)
            return v if v is not None else None
        except Exception as exc:
            raise StorageError(f"Redis get failed for key {key}: {exc}") from exc

    def delete(self, key: str) -> None:
        try:
            self._client.delete(key)
        except Exception as exc:
            raise StorageError(f"Redis delete failed for key {key}: {exc}") from exc
```

---

#### Exact code to add for in-memory storage

Create `tasker/infrastructure/memory_storage.py` with the exact content below.

```python
# tasker/infrastructure/memory_storage.py
from __future__ import annotations
import threading
import time
from typing import Optional, Dict, Tuple
from tasker.application.ports import StoragePort

class MemoryStorage(StoragePort):
    """
    In-memory StoragePort implementation with TTL support.

    - Thread-safe.
    - put stores bytes and optional TTL (seconds).
    - get returns bytes or None.
    - delete removes key if exists.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # key -> (value_bytes, expire_at_timestamp_or_None)
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
                # expired
                del self._store[key]
                return None
            return value

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
```

---

#### Exact code to add for cache utilities

Create `tasker/application/cache_utils.py` with the exact content below.

```python
# tasker/application/cache_utils.py
from __future__ import annotations
from typing import Callable, Optional, Any
import json
from tasker.application.ports import StoragePort
from tasker.application.exceptions import StorageError
from functools import wraps

def get_or_set(storage: StoragePort, key: str, factory: Callable[[], bytes], ttl_seconds: Optional[int] = None) -> bytes:
    """
    Retrieve bytes from storage by key or call factory() to produce bytes, store them with TTL, and return.
    Raises StorageError on storage failures.
    """
    try:
        v = storage.get(key)
    except Exception as exc:
        raise StorageError(f"Storage get failed for key {key}: {exc}") from exc
    if v is not None:
        return v
    # produce value
    val = factory()
    try:
        storage.put(key, val, ttl_seconds=ttl_seconds)
    except Exception as exc:
        raise StorageError(f"Storage put failed for key {key}: {exc}") from exc
    return val

def memoize(ttl_seconds: Optional[int] = None):
    """
    Decorator to memoize function results (JSON-serializable) into StoragePort passed as keyword arg 'storage'.
    The decorated function must accept a 'storage' keyword argument of type StoragePort.
    The cache key is derived from function name and args/kwargs.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            storage = kwargs.get("storage")
            if storage is None:
                # no storage provided; call function directly
                return fn(*args, **kwargs)
            # build key
            key_parts = [fn.__module__, fn.__name__, json.dumps(args, default=str, sort_keys=True), json.dumps(kwargs, default=str, sort_keys=True)]
            key = "cache:" + ":".join(key_parts)
            def factory():
                res = fn(*args, **kwargs)
                # serialize to bytes
                return json.dumps(res, default=str).encode("utf-8")
            raw = get_or_set(storage, key, factory, ttl_seconds=ttl_seconds)
            return json.loads(raw.decode("utf-8"))
        return wrapper
    return decorator
```

---

#### Exact Docker Compose for Redis integration tests

Create `docker-compose.redis.yml` at repo root with the exact content below.

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

**`tests/infrastructure/test_memory_storage_unit.py`**

```python
# tests/infrastructure/test_memory_storage_unit.py
import time
from tasker.infrastructure.memory_storage import MemoryStorage

def test_memory_put_get_delete_and_ttl():
    s = MemoryStorage()
    s.put("k1", b"v1")
    assert s.get("k1") == b"v1"
    s.delete("k1")
    assert s.get("k1") is None

    s.put("k2", b"v2", ttl_seconds=1)
    assert s.get("k2") == b"v2"
    time.sleep(1.1)
    assert s.get("k2") is None
```

**`tests/infrastructure/test_redis_storage_unit.py`**

```python
# tests/infrastructure/test_redis_storage_unit.py
from unittest.mock import MagicMock, patch
from tasker.infrastructure.redis_storage import RedisStorage
from tasker.application.exceptions import StorageError

@patch("tasker.infrastructure.redis_storage.redis")
def test_redis_storage_put_get_delete(mock_redis_module):
    client = MagicMock()
    mock_redis_module.from_url.return_value = client
    client.ping.return_value = True
    client.get.return_value = b"v"
    rs = RedisStorage(url="redis://localhost:6379/0")
    rs.put("k", b"v", ttl_seconds=10)
    client.setex.assert_called()
    assert rs.get("k") == b"v"
    rs.delete("k")
    client.delete.assert_called_with("k")

@patch("tasker.infrastructure.redis_storage.redis")
def test_redis_storage_connection_failure(mock_redis_module):
    mock_redis_module.from_url.side_effect = Exception("conn fail")
    try:
        RedisStorage(url="redis://bad")
        assert False, "Expected StorageError"
    except StorageError:
        pass
```

**`tests/application/test_cache_utils_unit.py`**

```python
# tests/application/test_cache_utils_unit.py
from tasker.application.cache_utils import get_or_set, memoize
from tasker.infrastructure.memory_storage import MemoryStorage

def test_get_or_set_uses_factory_and_caches():
    s = MemoryStorage()
    called = {"n": 0}
    def factory():
        called["n"] += 1
        return b"data"
    v1 = get_or_set(s, "k", factory, ttl_seconds=1)
    assert v1 == b"data"
    v2 = get_or_set(s, "k", factory, ttl_seconds=1)
    assert called["n"] == 1

def test_memoize_decorator_serializes_and_reads_back():
    s = MemoryStorage()
    @memoize(ttl_seconds=1)
    def compute(x, storage=None):
        return {"x": x}
    res = compute(3, storage=s)
    assert res == {"x": 3}
    res2 = compute(3, storage=s)
    assert res2 == {"x": 3}
```

---

#### Exact integration test to add

**`tests/integration/test_redis_storage_integration.py`**

```python
# tests/integration/test_redis_storage_integration.py
import os
import time
import pytest
from tasker.infrastructure.redis_storage import RedisStorage

pytestmark = pytest.mark.integration

def _skip_if_no_redis():
    if os.getenv("TASKER_REDIS_URL") is None:
        pytest.skip("Redis not configured; set TASKER_REDIS_URL or run docker-compose.redis.yml")

def test_redis_put_get_delete_integration():
    _skip_if_no_redis()
    url = os.getenv("TASKER_REDIS_URL", "redis://localhost:6379/0")
    s = RedisStorage(url=url)
    s.put("ik", b"iv", ttl_seconds=2)
    assert s.get("ik") == b"iv"
    time.sleep(2.1)
    assert s.get("ik") is None
    s.put("ik2", b"v2")
    assert s.get("ik2") == b"v2"
    s.delete("ik2")
    assert s.get("ik2") is None
```

---

#### Exact documentation to add

Create `tasker/infrastructure/STORAGE.md` with the exact content below.

```
Storage adapters and caching utilities

Adapters
- RedisStorage (tasker/infrastructure/redis_storage.py)
  - Uses redis-py client.
  - Methods: put(key, bytes, ttl_seconds), get(key) -> Optional[bytes], delete(key).
  - Raises StorageError on connection or operation failures.
  - Configure via TASKER_REDIS_URL (default redis://localhost:6379/0).

- MemoryStorage (tasker/infrastructure/memory_storage.py)
  - In-memory TTL-capable store for local dev and tests.
  - Thread-safe.

Caching utilities
- get_or_set(storage, key, factory, ttl_seconds)
  - Retrieves bytes or calls factory() to produce bytes and stores them.

- memoize(ttl_seconds)
  - Decorator for functions that accept a 'storage' kwarg and return JSON-serializable results.
  - Stores serialized JSON bytes under deterministic key derived from function name and args.

Examples
- Using MemoryStorage:
  from tasker.infrastructure.memory_storage import MemoryStorage
  s = MemoryStorage()
  s.put("k", b"v", ttl_seconds=60)
  v = s.get("k")

- Using get_or_set:
  val = get_or_set(s, "k", lambda: b"computed", ttl_seconds=30)

Integration tests
- Use docker-compose.redis.yml to start Redis:
  docker compose -f docker-compose.redis.yml up -d
- Set TASKER_REDIS_URL if Redis is not on default host/port.
```

---

#### Exact wiring modification

Modify `tasker/cli/wiring.py` to include storage wiring. Replace or add the following excerpt exactly.

```python
# tasker/cli/wiring.py (excerpt)
from tasker.infrastructure.memory_storage import MemoryStorage
from tasker.infrastructure.redis_storage import RedisStorage
import os

def build_default_container() -> Container:
    # existing wiring...
    # storage selection
    redis_url = os.getenv("TASKER_REDIS_URL")
    if redis_url:
        try:
            storage = RedisStorage(url=redis_url)
        except Exception:
            storage = MemoryStorage()
    else:
        storage = MemoryStorage()
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
    )
```

---

#### Exact commands the agent must run

```bash
git checkout -b feature/storage-redis-memory
# create files as specified
python -m pip install -e .
# run unit tests
pytest tests/infrastructure/test_memory_storage_unit.py -q
pytest tests/infrastructure/test_redis_storage_unit.py -q
pytest tests/application/test_cache_utils_unit.py -q
# optional: run integration tests with Redis
docker compose -f docker-compose.redis.yml up -d
export TASKER_REDIS_URL="redis://localhost:6379/0"
pytest tests/integration/test_redis_storage_integration.py -q -m integration || true
# commit and push
git add tasker/infrastructure/redis_storage.py tasker/infrastructure/memory_storage.py tasker/application/cache_utils.py tasker/infrastructure/STORAGE.md docker-compose.redis.yml tests/infrastructure tests/application tests/integration
git commit -m "feat(storage): add Redis and Memory StoragePort adapters and caching utilities with tests"
git push origin feature/storage-redis-memory
```

---

#### PR body exact text to paste

```
Summary:
- Added RedisStorage adapter at tasker/infrastructure/redis_storage.py implementing StoragePort.
- Added MemoryStorage adapter at tasker/infrastructure/memory_storage.py for local dev and tests.
- Added caching utilities at tasker/application/cache_utils.py: get_or_set and memoize decorator.
- Added integration Docker Compose file docker-compose.redis.yml for Redis.
- Added unit tests and integration test for storage and cache utilities.
- Updated CLI wiring to select Redis when TASKER_REDIS_URL is set, otherwise use MemoryStorage.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran unit tests for memory storage, redis storage (mocked), and cache utils.
3. Optionally started Redis via docker compose and ran integration test.
4. Verified wiring uses Redis when TASKER_REDIS_URL is set.

Files changed:
- tasker/infrastructure/redis_storage.py
- tasker/infrastructure/memory_storage.py
- tasker/application/cache_utils.py
- tasker/infrastructure/STORAGE.md
- docker-compose.redis.yml
- tests/infrastructure/test_memory_storage_unit.py
- tests/infrastructure/test_redis_storage_unit.py
- tests/application/test_cache_utils_unit.py
- tests/integration/test_redis_storage_integration.py

Notes:
- Redis client is optional; MemoryStorage provides deterministic behavior for CI and local development.
- StorageError is raised for adapter failures and maps to application-level error handling.
```

---

#### Acceptance criteria (must be satisfied exactly)
- `tasker/infrastructure/redis_storage.py` exists and implements `put`, `get`, `delete` with `StorageError` semantics.
- `tasker/infrastructure/memory_storage.py` exists and implements `put`, `get`, `delete` with TTL and thread-safety.
- `tasker/application/cache_utils.py` exists and provides `get_or_set` and `memoize` with the exact signatures.
- Unit tests `tests/infrastructure/test_memory_storage_unit.py`, `tests/infrastructure/test_redis_storage_unit.py`, and `tests/application/test_cache_utils_unit.py` exist and pass.
- Integration test `tests/integration/test_redis_storage_integration.py` passes when Redis is available via `docker-compose.redis.yml`.
- `tasker/infrastructure/STORAGE.md` documents behavior and examples.
- `tasker/cli/wiring.py` is updated to wire `storage` into `Container` using Redis when `TASKER_REDIS_URL` is set, otherwise MemoryStorage.
- Branch `feature/storage-redis-memory` created and PR opened with the exact PR body above.

---

#### Labels to apply on GitHub
- `infra`
- `cache`
- `redis`
- `medium-priority`

---

#### Estimated effort
**Small–Medium (S–M)** — expected to take **1–3 hours** depending on whether Redis is available locally.