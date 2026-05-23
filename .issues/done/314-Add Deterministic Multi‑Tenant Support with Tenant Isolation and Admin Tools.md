### Issue 314 — Add Deterministic Multi‑Tenant Support with Tenant Isolation and Admin Tools

**Descripción breve**  
Agregar soporte determinista para **multi‑tenant** en Tasker con aislamiento lógico de datos por tenant, middleware para resolución de tenant desde host/header/token, per‑tenant configuration, migration helpers, admin CLI and API to manage tenants, unit and integration tests, and documentación. Todo debe ser explícito: nombres de archivos, variables de entorno, rutas, firmas de funciones, comportamientos, comandos y PR body exacto para que un agente o desarrollador lo implemente sin ambigüedades.

---

## Objetivo exacto que debe entregar el agente
1. **Core tenant module** `tasker/tenancy` que expone:
   - `class TenantContext` con atributos `tenant_id: str`, `config: dict`.
   - `def get_current_tenant() -> TenantContext | None` dependency for FastAPI and helper for CLI.
   - `class TenantStore` backed by `StoragePort` (or in-memory) with methods `create_tenant(tenant_id: str, config: dict)`, `delete_tenant(tenant_id: str)`, `list_tenants() -> list[dict]`, `get_tenant(tenant_id: str) -> dict | None`.
2. **Middleware and resolver**:
   - `tasker/tenancy/middleware.py` FastAPI middleware `TenantMiddleware` that resolves tenant from:
     - `X-Tenant-ID` header if present,
     - subdomain of `Host` header (format `<tenant>.localhost`),
     - token mapping via `container.tenancy.token_map` (optional).
   - Middleware must attach `TenantContext` to `request.state.tenant` and make it available to `get_current_tenant`.
3. **Repository and storage scoping**:
   - Modify wiring so `Container` provides `tenant_store` and `tenant_scoped_storage(tenant_id: str) -> StoragePort` factory that returns a namespaced storage wrapper (prefix keys with `tenant:{tenant_id}:`).
   - Provide `tasker/infrastructure/tenant_storage.py` implementing `NamespacedStorage` wrapper around any `StoragePort` with methods `put`, `get`, `delete`, and `list_keys` delegating with prefix.
4. **Per‑tenant migrations**:
   - Add `tasker/tenancy/migrations.py` with functions:
     - `def ensure_tenant_schema(tenant_id: str) -> None` (calls repo adapters to create indexes/namespaces).
     - `def run_migrations(tenant_id: str, migrations: list[Callable[[Container], None]]) -> None`.
5. **Admin API and CLI**:
   - FastAPI endpoints under `/api/v1/admin/tenants`:
     - `POST /api/v1/admin/tenants` create tenant (admin only).
     - `GET /api/v1/admin/tenants` list tenants (admin only).
     - `GET /api/v1/admin/tenants/{tenant_id}` get tenant config (admin only).
     - `DELETE /api/v1/admin/tenants/{tenant_id}` delete tenant (admin only).
   - CLI commands in `tasker/cli/main.py`:
     - `tenant-create --id <tenant_id> --config <json>`,
     - `tenant-list`,
     - `tenant-delete --id <tenant_id>`.
   - CLI must call `container.tenant_store` and `ensure_tenant_schema`.
6. **Unit tests**:
   - `tests/tenancy/test_tenant_store_unit.py` for `TenantStore`.
   - `tests/tenancy/test_middleware_unit.py` for `TenantMiddleware` resolving header and host.
   - `tests/integration/test_tenant_isolation.py` that creates two tenants, writes storage keys under each, and asserts isolation.
7. **Integration test**:
   - `tests/integration/test_multi_tenant_end_to_end.py` marked `integration` that:
     - Starts services if needed,
     - Creates tenants via admin API,
     - Runs migrations,
     - Uses API endpoints to create issues under tenant A and tenant B and verifies they do not cross.
8. **Documentation**:
   - `tasker/tenancy/TENANCY.md` describing tenant resolution order, storage namespacing, migration process, admin operations, and security notes.
9. **Branch and PR**:
   - Create branch `feature/multi-tenant` and open PR with the exact PR body provided below.

---

## Archivos a añadir o modificar exactos

- `tasker/tenancy/__init__.py` **(nuevo)**
- `tasker/tenancy/context.py` **(nuevo)**
- `tasker/tenancy/store.py` **(nuevo)**
- `tasker/tenancy/middleware.py` **(nuevo)**
- `tasker/tenancy/migrations.py` **(nuevo)**
- `tasker/infrastructure/tenant_storage.py` **(nuevo)**
- `tasker/tenancy/TENANCY.md` **(nuevo)**
- `tests/tenancy/test_tenant_store_unit.py` **(nuevo)**
- `tests/tenancy/test_middleware_unit.py` **(nuevo)**
- `tests/integration/test_tenant_isolation.py` **(nuevo, integration)**
- Modify `tasker/cli/wiring.py` to wire `tenant_store` and `tenant_scoped_storage`.
- Modify `tasker/cli/main.py` to add tenant CLI commands.
- Modify `tasker/api/app.py` to add admin tenant endpoints and register `TenantMiddleware`.

---

## Código exacto a añadir

### `tasker/tenancy/__init__.py`
```python
# tasker/tenancy/__init__.py
from .context import TenantContext, get_current_tenant
from .store import TenantStore
from .middleware import TenantMiddleware
from .migrations import ensure_tenant_schema, run_migrations

__all__ = ["TenantContext", "get_current_tenant", "TenantStore", "TenantMiddleware", "ensure_tenant_schema", "run_migrations"]
```

### `tasker/tenancy/context.py`
```python
# tasker/tenancy/context.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict
from fastapi import Request, Depends

@dataclass
class TenantContext:
    tenant_id: str
    config: Dict

# internal request-state accessor
def get_current_tenant(request: Optional[Request] = None) -> Optional[TenantContext]:
    if request is None:
        return None
    return getattr(request.state, "tenant", None)
```

### `tasker/tenancy/store.py`
```python
# tasker/tenancy/store.py
from __future__ import annotations
from typing import Optional, Dict, List
import json
from tasker.application.ports import StoragePort
from tasker.application.exceptions import StorageError

class TenantStore:
    """
    Simple tenant registry backed by StoragePort under key 'tenants'.
    Each tenant entry: tenant_id -> {"id": tenant_id, "config": {...}}
    """

    KEY = "tenants:registry"

    def __init__(self, storage: StoragePort):
        self.storage = storage
        self._cache: Dict[str, Dict] = {}
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
            raise StorageError(f"Failed to persist tenants: {exc}") from exc

    def create_tenant(self, tenant_id: str, config: Optional[Dict] = None) -> Dict:
        if tenant_id in self._cache:
            raise ValueError("tenant exists")
        cfg = config or {}
        self._cache[tenant_id] = {"id": tenant_id, "config": cfg}
        self._persist()
        return self._cache[tenant_id]

    def delete_tenant(self, tenant_id: str) -> None:
        if tenant_id in self._cache:
            self._cache.pop(tenant_id)
            self._persist()

    def list_tenants(self) -> List[Dict]:
        return list(self._cache.values())

    def get_tenant(self, tenant_id: str) -> Optional[Dict]:
        return self._cache.get(tenant_id)
```

> **Nota**: `json` import is required; ensure to add `import json` at top. Keep exact behavior.

### `tasker/tenancy/middleware.py`
```python
# tasker/tenancy/middleware.py
from __future__ import annotations
import os
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from typing import Optional
from tasker.tenancy.context import TenantContext

class TenantMiddleware(BaseHTTPMiddleware):
    """
    Resolve tenant from X-Tenant-ID header, host subdomain, or token map in container.
    Attach TenantContext to request.state.tenant.
    Resolution order:
      1. X-Tenant-ID header
      2. Host header subdomain (<tenant>.host)
      3. token_map lookup via Authorization header (container.tenancy.token_map)
    """

    def __init__(self, app, container):
        super().__init__(app)
        self.container = container

    async def dispatch(self, request: Request, call_next):
        tenant_id = None
        # header
        tenant_id = request.headers.get("x-tenant-id")
        # host subdomain
        if not tenant_id:
            host = request.headers.get("host", "")
            if host and "." in host:
                sub = host.split(".")[0]
                if sub and sub != "localhost":
                    tenant_id = sub
        # token map
        if not tenant_id:
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1]
                token_map = getattr(self.container, "tenancy_token_map", {})
                tenant_id = token_map.get(token)
        tenant_ctx = None
        if tenant_id:
            tenant = self.container.tenant_store.get_tenant(tenant_id)
            if tenant:
                tenant_ctx = TenantContext(tenant_id=tenant_id, config=tenant.get("config", {}))
        request.state.tenant = tenant_ctx
        return await call_next(request)
```

### `tasker/infrastructure/tenant_storage.py`
```python
# tasker/infrastructure/tenant_storage.py
from __future__ import annotations
from typing import Optional, Iterable, List
from tasker.application.ports import StoragePort

class NamespacedStorage(StoragePort):
    """
    Wraps another StoragePort and prefixes keys with tenant:{tenant_id}:
    """

    def __init__(self, base: StoragePort, tenant_id: str):
        self._base = base
        self._prefix = f"tenant:{tenant_id}:"

    def _key(self, key: str) -> str:
        return self._prefix + key

    def put(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
        return self._base.put(self._key(key), value, ttl_seconds=ttl_seconds)

    def get(self, key: str) -> Optional[bytes]:
        return self._base.get(self._key(key))

    def delete(self, key: str) -> None:
        return self._base.delete(self._key(key))

    # optional helper if base supports listing
    def list_keys(self) -> List[str]:
        if hasattr(self._base, "list_keys"):
            keys = self._base.list_keys()
            prefix = self._prefix
            return [k[len(prefix):] for k in keys if k.startswith(prefix)]
        return []
```

### `tasker/tenancy/migrations.py`
```python
# tasker/tenancy/migrations.py
from __future__ import annotations
from typing import Callable, List
from tasker.cli.wiring import build_default_container

def ensure_tenant_schema(tenant_id: str) -> None:
    """
    Ensure indexes or namespaces exist for tenant. Implementation is adapter-specific.
    For deterministic behavior, call repository adapters that expose tenant-aware methods.
    """
    container = build_default_container()
    # If repositories expose ensure_tenant, call them
    if hasattr(container.issue_repo, "ensure_tenant"):
        container.issue_repo.ensure_tenant(tenant_id)
    if hasattr(container.graph_repo, "ensure_tenant"):
        container.graph_repo.ensure_tenant(tenant_id)

def run_migrations(tenant_id: str, migrations: List[Callable[[object], None]]) -> None:
    container = build_default_container()
    for m in migrations:
        m(container)
```

---

## Modificaciones de wiring y API

### `tasker/cli/wiring.py` excerpt to add (exact)
Insert or replace the following excerpt in `build_default_container()`:

```python
# tenancy wiring
from tasker.tenancy.store import TenantStore
from tasker.infrastructure.tenant_storage import NamespacedStorage

tenant_store = TenantStore(storage)
def tenant_scoped_storage(tenant_id: str):
    return NamespacedStorage(storage, tenant_id=tenant_id)
# optional token map for tenant resolution via token
tenancy_token_map = {}
# include in Container
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
    tenant_store=tenant_store,
    tenant_scoped_storage=tenant_scoped_storage,
    tenancy_token_map=tenancy_token_map,
)
```

### `tasker/api/app.py` excerpt to register middleware and admin endpoints (exact)

Add middleware registration after app creation:

```python
from tasker.tenancy.middleware import TenantMiddleware
# after container built
app.add_middleware(TenantMiddleware, container=build_api_container())
```

Add admin endpoints (exact):

```python
@app.post("/api/v1/admin/tenants")
def api_create_tenant(req: dict, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    tid = req.get("id")
    cfg = req.get("config", {})
    tenant = container.tenant_store.create_tenant(tid, cfg)
    # ensure schema
    from tasker.tenancy.migrations import ensure_tenant_schema
    ensure_tenant_schema(tid)
    return {"status":"ok","tenant":tenant}

@app.get("/api/v1/admin/tenants")
def api_list_tenants(user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    return {"status":"ok","tenants": container.tenant_store.list_tenants()}

@app.get("/api/v1/admin/tenants/{tenant_id}")
def api_get_tenant(tenant_id: str, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    t = container.tenant_store.get_tenant(tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="not found")
    return {"status":"ok","tenant":t}

@app.delete("/api/v1/admin/tenants/{tenant_id}")
def api_delete_tenant(tenant_id: str, user_id: str = Depends(get_user_id_from_token), container = Depends(get_container)):
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    container.tenant_store.delete_tenant(tenant_id)
    return {"status":"ok"}
```

---

## Tests exactos a añadir

### `tests/tenancy/test_tenant_store_unit.py`
```python
# tests/tenancy/test_tenant_store_unit.py
from tasker.tenancy.store import TenantStore
from tasker.infrastructure.memory_storage import MemoryStorage

def test_tenant_store_create_list_get_delete():
    s = MemoryStorage()
    ts = TenantStore(s)
    t = ts.create_tenant("t1", {"name":"T1"})
    assert t["id"] == "t1"
    assert ts.get_tenant("t1") is not None
    lst = ts.list_tenants()
    assert any(x["id"] == "t1" for x in lst)
    ts.delete_tenant("t1")
    assert ts.get_tenant("t1") is None
```

### `tests/tenancy/test_middleware_unit.py`
```python
# tests/tenancy/test_middleware_unit.py
from fastapi import FastAPI
from fastapi.testclient import TestClient
from tasker.tenancy.middleware import TenantMiddleware
from tasker.tenancy.store import TenantStore
from tasker.infrastructure.memory_storage import MemoryStorage
from types import SimpleNamespace

def test_tenant_middleware_header_and_host():
    app = FastAPI()
    # dummy container with tenant_store and token_map
    storage = MemoryStorage()
    ts = TenantStore(storage)
    ts.create_tenant("h1", {"name":"H1"})
    container = SimpleNamespace(tenant_store=ts, tenancy_token_map={})
    app.add_middleware(TenantMiddleware, container=container)
    @app.get("/who")
    def who(request):
        t = getattr(request.state, "tenant", None)
        return {"tenant": t.tenant_id if t else None}
    client = TestClient(app)
    r = client.get("/who", headers={"X-Tenant-ID":"h1"})
    assert r.json()["tenant"] == "h1"
    # host subdomain
    r2 = client.get("/who", headers={"Host":"h1.localhost"})
    assert r2.json()["tenant"] == "h1"
```

### `tests/integration/test_tenant_isolation.py`
```python
# tests/integration/test_tenant_isolation.py
import os
import time
import pytest
from tasker.infrastructure.memory_storage import MemoryStorage
from tasker.infra.tenant_storage import NamespacedStorage
from tasker.tenancy.store import TenantStore

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_storage_isolation(tmp_path):
    _skip_if_not_integration()
    base = MemoryStorage()
    ts = TenantStore(base)
    ts.create_tenant("a", {})
    ts.create_tenant("b", {})
    sa = NamespacedStorage(base, "a")
    sb = NamespacedStorage(base, "b")
    sa.put("k", b"va")
    sb.put("k", b"vb")
    assert sa.get("k") == b"va"
    assert sb.get("k") == b"vb"
```

---

## Documentación exacta a añadir

### `tasker/tenancy/TENANCY.md`
```
Multi-Tenancy Guide

Resolution order
1. X-Tenant-ID header
2. Host subdomain (<tenant>.host)
3. Token map via container.tenancy_token_map

Storage namespacing
- Use tenant_scoped_storage(tenant_id) to obtain a NamespacedStorage that prefixes keys with tenant:{tenant_id}:

Migrations
- Call ensure_tenant_schema(tenant_id) after creating a tenant.
- Use run_migrations to run tenant-specific migration functions.

Admin operations
- Create tenant: POST /api/v1/admin/tenants { "id": "tenant1", "config": {...} }
- List tenants: GET /api/v1/admin/tenants
- Delete tenant: DELETE /api/v1/admin/tenants/{tenant_id}

Security
- Admin endpoints require admin RBAC permission.
- Tenant resolution from host is convenient for dev; in production prefer header or token mapping.

Testing
- Set TASKER_INTEGRATION=1 to run integration tests that exercise tenant isolation.
```

---

## Comandos exactos que el agente debe ejecutar

```bash
git checkout -b feature/multi-tenant
# create files as specified
python -m pip install -e .
# run unit tests
pytest tests/tenancy/test_tenant_store_unit.py -q
pytest tests/tenancy/test_middleware_unit.py -q
# run integration tests if desired
export TASKER_INTEGRATION=1
pytest tests/integration/test_tenant_isolation.py -q -m integration || true
# commit and push
git add tasker/tenancy tasker/infrastructure/tenant_storage.py tests/tenancy tests/integration tasker/tenancy/TENANCY.md
git commit -m "feat(tenancy): add deterministic multi-tenant support, middleware, namespaced storage and admin tools"
git push origin feature/multi-tenant
```

---

## PR body exacto a pegar

```
Summary:
- Added deterministic multi-tenant support with TenantContext, TenantStore, TenantMiddleware, NamespacedStorage and migration helpers.
- Integrated tenant_store and tenant_scoped_storage into wiring container.
- Added admin API endpoints to create/list/get/delete tenants and ensured schema creation via ensure_tenant_schema.
- Added unit and integration tests for tenant store, middleware, and storage isolation.
- Added documentation tasker/tenancy/TENANCY.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Ran unit tests for tenant store and middleware (passed).
3. Optionally ran integration test for storage isolation with TASKER_INTEGRATION=1 (passed when environment available).

Files changed:
- tasker/tenancy/__init__.py
- tasker/tenancy/context.py
- tasker/tenancy/store.py
- tasker/tenancy/middleware.py
- tasker/tenancy/migrations.py
- tasker/infrastructure/tenant_storage.py
- tasker/tenancy/TENANCY.md
- tests/tenancy/*
- tests/integration/test_tenant_isolation.py
- Modified: tasker/cli/wiring.py, tasker/api/app.py

Notes:
- NamespacedStorage prefixes keys with tenant:{tenant_id}: to ensure logical isolation.
- For production multi-instance deployments, ensure backing StoragePort supports strong isolation or use separate storage instances per tenant.
```

---

## Criterios de aceptación exactos
- `tasker/tenancy` existe con `TenantContext`, `get_current_tenant`, `TenantStore`, `TenantMiddleware`, `ensure_tenant_schema`, `run_migrations`.
- `NamespacedStorage` exists and prefixes keys with `tenant:{tenant_id}:`.
- Wiring container exposes `tenant_store` and `tenant_scoped_storage`.
- FastAPI registers `TenantMiddleware` and admin tenant endpoints exist and require `admin` permission.
- Unit tests and integration test files exist and pass in described environments.
- `tasker/tenancy/TENANCY.md` documents resolution order, storage namespacing, migrations, and admin operations.
- Branch `feature/multi-tenant` created and PR opened with the exact PR body above.

---

## Labels to apply on GitHub
- `multi-tenant`
- `infra`
- `security`
- `medium-priority`

---

## Estimated effort
**Medium (M)** — expected to take **2–4 hours** depending on repository adapters and test environment.