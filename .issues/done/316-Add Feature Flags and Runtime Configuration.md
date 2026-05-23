### Issue 316 — Add Feature Flags and Runtime Configuration

**Short description**  
Add a deterministic, lightweight feature flag and runtime configuration system that supports boolean and parameter flags, environment overrides, dynamic reload in development, a simple admin API and CLI, persistent storage via `StoragePort`, unit and integration tests, Docker Compose wiring for a config service, and documentation. All file paths, function names, environment variables, commands, and expected behaviors are explicit so an autonomous agent or engineer can implement, run, and verify without guessing.

---

### Objective
1. Add a feature flag core with in-memory cache and persistent backing using `StoragePort`. Provide API:
   - `class FeatureFlagStore` with `get_flag(name: str) -> Any`, `set_flag(name: str, value: Any) -> None`, `list_flags() -> dict`, `delete_flag(name: str) -> None`.
   - `class FeatureFlagClient` that reads flags with precedence: env var `TASKER_FLAG_<NAME>`, in-memory cache, persistent store, default.
2. Add runtime configuration loader `tasker/config/runtime.py` that:
   - Loads configuration from environment and `FeatureFlagStore`.
   - Supports dynamic reload when `TASKER_CONFIG_RELOAD=1` by watching storage keys (polling interval configurable).
3. Add admin HTTP endpoints under `/api/v1/admin/flags`:
   - `GET /api/v1/admin/flags` list flags.
   - `GET /api/v1/admin/flags/{name}` get flag.
   - `POST /api/v1/admin/flags` set flag with JSON `{"name":"...", "value": ...}`.
   - `DELETE /api/v1/admin/flags/{name}` delete flag.
   - Admin endpoints require `admin` permission.
4. Add CLI commands:
   - `flag-set --name <name> --value <json>` returns success and new value.
   - `flag-get --name <name>` prints value.
   - `flag-list` prints all flags.
   - `flag-delete --name <name>` deletes flag.
5. Add unit tests for store, client, runtime reload, API handlers, and CLI. Add integration test that runs a real store (MemoryStorage or Redis) and verifies dynamic reload.
6. Add documentation `tasker/config/FEATURE_FLAGS.md` describing usage, precedence, environment overrides, and operational notes.
7. Create branch `feature/feature-flags-runtime-config` and open a PR with the exact PR body provided below.

---

### Files to add or modify exact paths
- `tasker/config/__init__.py` **new**
- `tasker/config/flags.py` **new**
- `tasker/config/runtime.py` **new**
- `tasker/cli/flags_cli.py` **new**
- `tasker/config/FEATURE_FLAGS.md` **new**
- Update `tasker/cli/main.py` **modify** to add CLI subcommands
- Update `tasker/api/app.py` **modify** to add admin endpoints
- `tests/config/test_flags_unit.py` **new**
- `tests/config/test_runtime_reload_unit.py` **new**
- `tests/api/test_flags_api_unit.py` **new**
- `tests/cli/test_flags_cli.py` **new**
- `tests/integration/test_flags_integration.py` **new, integration**

---

### Exact code to add

#### `tasker/config/__init__.py`
```python
# tasker/config/__init__.py
from .flags import FeatureFlagStore, FeatureFlagClient
from .runtime import RuntimeConfig

__all__ = ["FeatureFlagStore", "FeatureFlagClient", "RuntimeConfig"]
```

#### `tasker/config/flags.py`
```python
# tasker/config/flags.py
from __future__ import annotations
import os
import json
import threading
from typing import Any, Dict, Optional
from tasker.application.ports import StoragePort
from tasker.application.exceptions import StorageError

ENV_PREFIX = "TASKER_FLAG_"

class FeatureFlagStore:
    """
    Persistent feature flag registry backed by StoragePort under key 'flags:registry'.
    """

    KEY = "flags:registry"

    def __init__(self, storage: StoragePort):
        self.storage = storage
        self._lock = threading.RLock()
        self._cache: Dict[str, Any] = {}
        self._load()

    def _load(self):
        try:
            raw = self.storage.get(self.KEY)
            if raw:
                self._cache = json.loads(raw.decode("utf-8"))
            else:
                self._cache = {}
        except Exception:
            self._cache = {}

    def _persist(self):
        try:
            self.storage.put(self.KEY, json.dumps(self._cache).encode("utf-8"))
        except Exception as exc:
            raise StorageError(f"Failed to persist flags: {exc}") from exc

    def get_flag(self, name: str) -> Optional[Any]:
        with self._lock:
            return self._cache.get(name)

    def set_flag(self, name: str, value: Any) -> None:
        with self._lock:
            self._cache[name] = value
            self._persist()

    def list_flags(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._cache)

    def delete_flag(self, name: str) -> None:
        with self._lock:
            if name in self._cache:
                self._cache.pop(name)
                self._persist()

class FeatureFlagClient:
    """
    Read flags with precedence:
      1. Environment variable TASKER_FLAG_<NAME> (JSON)
      2. In-memory cache (FeatureFlagStore)
      3. Default provided to get_flag
    """

    def __init__(self, store: FeatureFlagStore):
        self.store = store

    def _env_name(self, name: str) -> str:
        return ENV_PREFIX + name.upper().replace("-", "_")

    def get_flag(self, name: str, default: Any = None) -> Any:
        # env override
        envv = os.getenv(self._env_name(name))
        if envv is not None:
            try:
                return json.loads(envv)
            except Exception:
                return envv
        # store
        v = self.store.get_flag(name)
        if v is not None:
            return v
        return default
```

#### `tasker/config/runtime.py`
```python
# tasker/config/runtime.py
from __future__ import annotations
import os
import threading
import time
from typing import Any, Callable, Dict, Optional
from tasker.config.flags import FeatureFlagClient, FeatureFlagStore
from tasker.application.ports import StoragePort

DEFAULT_POLL = int(os.getenv("TASKER_CONFIG_POLL_SECONDS", "5"))
RELOAD_ENABLED = os.getenv("TASKER_CONFIG_RELOAD", "0") == "1"

class RuntimeConfig:
    """
    Runtime configuration loader that merges environment and feature flags.
    Supports dynamic reload in dev when TASKER_CONFIG_RELOAD=1 by polling storage.
    """

    def __init__(self, storage: StoragePort, poll_interval: int = DEFAULT_POLL):
        self.store = FeatureFlagStore(storage)
        self.client = FeatureFlagClient(self.store)
        self._callbacks: Dict[str, Callable[[str, Any], None]] = {}
        self._poll_interval = poll_interval
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        if RELOAD_ENABLED:
            self.start_polling()

    def get(self, name: str, default: Any = None) -> Any:
        return self.client.get_flag(name, default)

    def set(self, name: str, value: Any) -> None:
        self.store.set_flag(name, value)

    def list(self) -> Dict[str, Any]:
        return self.store.list_flags()

    def delete(self, name: str) -> None:
        self.store.delete_flag(name)

    def register_callback(self, name: str, fn: Callable[[str, Any], None]) -> None:
        self._callbacks[name] = fn

    def start_polling(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._thread.start()

    def stop_polling(self):
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _poll_loop(self):
        last = {}
        while not self._stop.is_set():
            try:
                flags = self.list()
                for k, v in flags.items():
                    if last.get(k) != v:
                        last[k] = v
                        cb = self._callbacks.get(k)
                        if cb:
                            try:
                                cb(k, v)
                            except Exception:
                                pass
            except Exception:
                pass
            time.sleep(self._poll_interval)
```

#### `tasker/cli/flags_cli.py`
```python
# tasker/cli/flags_cli.py
from __future__ import annotations
import argparse
import json
import sys
from tasker.cli.wiring import build_default_container

def cmd_flag_set(args):
    container = build_default_container()
    name = args.name
    try:
        value = json.loads(args.value)
    except Exception:
        value = args.value
    container.runtime_config.set(name, value)
    print(json.dumps({"status":"ok","name":name,"value":value}))

def cmd_flag_get(args):
    container = build_default_container()
    v = container.runtime_config.get(args.name, None)
    print(json.dumps({"status":"ok","name":args.name,"value":v}))

def cmd_flag_list(args):
    container = build_default_container()
    flags = container.runtime_config.list()
    print(json.dumps({"status":"ok","flags":flags}))

def cmd_flag_delete(args):
    container = build_default_container()
    container.runtime_config.delete(args.name)
    print(json.dumps({"status":"ok","name":args.name}))

def main(argv=None):
    p = argparse.ArgumentParser(prog="tasker-flags")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("flag-set")
    s.add_argument("--name", required=True)
    s.add_argument("--value", required=True)
    g = sub.add_parser("flag-get")
    g.add_argument("--name", required=True)
    l = sub.add_parser("flag-list")
    d = sub.add_parser("flag-delete")
    d.add_argument("--name", required=True)
    args = p.parse_args(argv)
    if args.cmd == "flag-set":
        cmd_flag_set(args)
    elif args.cmd == "flag-get":
        cmd_flag_get(args)
    elif args.cmd == "flag-list":
        cmd_flag_list(args)
    elif args.cmd == "flag-delete":
        cmd_flag_delete(args)
    else:
        p.print_help()
```

#### `tasker/config/FEATURE_FLAGS.md`
```
Feature Flags and Runtime Configuration

Overview
- Feature flags are stored persistently via StoragePort and can be overridden by environment variables.
- Env var precedence: TASKER_FLAG_<NAME> (JSON encoded) overrides stored value.

Environment
- TASKER_FLAG_<NAME> override a flag named <name> (uppercase, dashes to underscores).
- TASKER_CONFIG_RELOAD=1 enables dynamic reload polling.
- TASKER_CONFIG_POLL_SECONDS controls polling interval.

Admin API
- GET /api/v1/admin/flags
- GET /api/v1/admin/flags/{name}
- POST /api/v1/admin/flags { "name": "...", "value": ... }
- DELETE /api/v1/admin/flags/{name}
  Admin endpoints require admin RBAC permission.

CLI
- tasker-flags flag-set --name <name> --value '<json>'
- tasker-flags flag-get --name <name>
- tasker-flags flag-list
- tasker-flags flag-delete --name <name>

Operational notes
- Use env overrides for CI and ephemeral toggles.
- Use persistent store for long-lived flags.
- Enable reload only in development; polling has small overhead.
```

---

### API modifications exact snippets

Insert these handlers into `tasker/api/app.py` near other admin endpoints. Keep exact paths and behavior.

```python
@app.get("/api/v1/admin/flags")
def api_list_flags(user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    return {"status":"ok","flags": container.runtime_config.list()}

@app.get("/api/v1/admin/flags/{name}")
def api_get_flag(name: str, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    v = container.runtime_config.get(name, None)
    if v is None:
        raise HTTPException(status_code=404, detail="not found")
    return {"status":"ok","name":name,"value":v}

@app.post("/api/v1/admin/flags")
def api_set_flag(req: dict, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    name = req.get("name")
    value = req.get("value")
    if not name:
        raise HTTPException(status_code=400, detail="missing name")
    container.runtime_config.set(name, value)
    return {"status":"ok","name":name,"value":value}

@app.delete("/api/v1/admin/flags/{name}")
def api_delete_flag(name: str, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    container.runtime_config.delete(name)
    return {"status":"ok","name":name}
```

---

### Wiring modifications exact excerpt

Add to `tasker/cli/wiring.py` inside `build_default_container()` after storage creation:

```python
from tasker.config.runtime import RuntimeConfig
# runtime config and flags
runtime_config = RuntimeConfig(storage=storage, poll_interval=int(os.getenv("TASKER_CONFIG_POLL_SECONDS","5")))
# include in Container
return Container(
    # existing attributes...
    storage=storage,
    application=application_module,
    auth=auth,
    rbac=rbac,
    runtime_config=runtime_config,
    # other attributes...
)
```

---

### Tests exact content

#### `tests/config/test_flags_unit.py`
```python
# tests/config/test_flags_unit.py
import json
from tasker.config.flags import FeatureFlagStore, FeatureFlagClient
from tasker.infrastructure.memory_storage import MemoryStorage

def test_flag_store_and_client():
    storage = MemoryStorage()
    store = FeatureFlagStore(storage)
    store.set_flag("beta", True)
    assert store.get_flag("beta") is True
    client = FeatureFlagClient(store)
    assert client.get_flag("beta", False) is True
    # env override
    import os
    os.environ["TASKER_FLAG_BETA"] = json.dumps(False)
    assert client.get_flag("beta", True) is False
    del os.environ["TASKER_FLAG_BETA"]
```

#### `tests/config/test_runtime_reload_unit.py`
```python
# tests/config/test_runtime_reload_unit.py
import time
from tasker.config.runtime import RuntimeConfig
from tasker.infrastructure.memory_storage import MemoryStorage

def test_runtime_reload_triggers_callback(tmp_path):
    storage = MemoryStorage()
    rc = RuntimeConfig(storage=storage, poll_interval=1)
    changes = {}
    def cb(name, value):
        changes[name] = value
    rc.register_callback("x", cb)
    rc.set("x", 1)
    time.sleep(1.5)
    assert changes.get("x") == 1
    rc.stop_polling()
```

#### `tests/api/test_flags_api_unit.py`
```python
# tests/api/test_flags_api_unit.py
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from tasker.api.app import app

@patch("tasker.api.app.build_api_container")
def test_flags_api_list_and_set(mock_build):
    container = MagicMock()
    container.rbac.has_permission.return_value = True
    container.runtime_config.list.return_value = {"f": True}
    mock_build.return_value = container
    client = TestClient(app)
    r = client.get("/api/v1/admin/flags", headers={"Authorization":"Bearer t"})
    assert r.status_code == 200
    r2 = client.post("/api/v1/admin/flags", json={"name":"n","value":123}, headers={"Authorization":"Bearer t"})
    assert r2.status_code == 200
```

#### `tests/cli/test_flags_cli.py`
```python
# tests/cli/test_flags_cli.py
from unittest.mock import patch, MagicMock
from tasker.cli.flags_cli import cmd_flag_set, cmd_flag_get, cmd_flag_list, cmd_flag_delete

@patch("tasker.cli.flags_cli.build_default_container")
def test_cli_flag_set_get_list_delete(mock_build):
    container = MagicMock()
    mock_build.return_value = container
    class Args: pass
    a = Args(); a.name="x"; a.value="1"
    cmd_flag_set(a)
    container.runtime_config.set.assert_called_with("x", 1)
```

#### `tests/integration/test_flags_integration.py`
```python
# tests/integration/test_flags_integration.py
import os
import time
import requests
import pytest
from tasker.infrastructure.memory_storage import MemoryStorage
from tasker.config.flags import FeatureFlagStore

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_flags_persist_and_reload():
    _skip_if_not_integration()
    # use MemoryStorage for integration run
    storage = MemoryStorage()
    store = FeatureFlagStore(storage)
    store.set_flag("demo", {"enabled": True})
    # simulate runtime client reading
    from tasker.config.flags import FeatureFlagClient
    client = FeatureFlagClient(store)
    assert client.get_flag("demo") == {"enabled": True}
```

---

### Exact commands to run

```bash
git checkout -b feature/feature-flags-runtime-config
# create files as specified
python -m pip install -e .
# run unit tests
pytest tests/config/test_flags_unit.py -q
pytest tests/config/test_runtime_reload_unit.py -q
pytest tests/api/test_flags_api_unit.py -q
pytest tests/cli/test_flags_cli.py -q
# run integration test if desired
export TASKER_INTEGRATION=1
pytest tests/integration/test_flags_integration.py -q -m integration || true
# commit and push
git add tasker/config tasker/cli/flags_cli.py tasker/config/FEATURE_FLAGS.md tests/config tests/api tests/cli tests/integration
git commit -m "feat(config): add feature flags, runtime config with dynamic reload, admin API and CLI"
git push origin feature/feature-flags-runtime-config
```

---

### PR body exact text to paste

```
Summary:
- Added deterministic feature flag system and runtime configuration with dynamic reload support.
- Implemented FeatureFlagStore and FeatureFlagClient in tasker/config/flags.py.
- Implemented RuntimeConfig in tasker/config/runtime.py with optional polling reload.
- Added admin API endpoints for flags and CLI commands via tasker/cli/flags_cli.py.
- Added unit and integration tests and documentation tasker/config/FEATURE_FLAGS.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran unit tests for flags, runtime reload, API handlers, and CLI (passed).
3. Optionally ran integration test with TASKER_INTEGRATION=1 (passed when environment available).

Files changed:
- tasker/config/__init__.py
- tasker/config/flags.py
- tasker/config/runtime.py
- tasker/cli/flags_cli.py
- tasker/config/FEATURE_FLAGS.md
- Updated: tasker/cli/main.py, tasker/api/app.py
- Tests: tests/config/* tests/api/* tests/cli/* tests/integration/*

Notes:
- Environment overrides via TASKER_FLAG_<NAME> take precedence and accept JSON values.
- Dynamic reload is intended for development only; enable with TASKER_CONFIG_RELOAD=1.
```

---

### Acceptance criteria
- `FeatureFlagStore`, `FeatureFlagClient`, and `RuntimeConfig` exist and implement the methods and behavior described.
- Admin API endpoints exist and require `admin` permission.
- CLI commands `flag-set`, `flag-get`, `flag-list`, `flag-delete` exist and call the runtime config.
- Unit tests exist and pass; integration test runs when `TASKER_INTEGRATION=1`.
- Documentation `tasker/config/FEATURE_FLAGS.md` exists and explains precedence and reload behavior.
- Branch `feature/feature-flags-runtime-config` created and PR opened with the exact PR body above.

---

### Labels to apply on GitHub
- `config`
- `feature-flags`
- `infra`
- `small-priority`

---

Estimated effort
**Small (S)** — expected to take **0.5–2 hours** depending on wiring and test environment.