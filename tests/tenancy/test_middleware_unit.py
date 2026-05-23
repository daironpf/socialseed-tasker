# tests/tenancy/test_middleware_unit.py
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from socialseed_tasker.tenancy.middleware import TenantMiddleware
from socialseed_tasker.tenancy.store import TenantStore
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from types import SimpleNamespace

def test_tenant_middleware_header_and_host():
    app = FastAPI()
    storage = MemoryStorage()
    ts = TenantStore(storage)
    ts.create_tenant("h1", {"name":"H1"})
    container = SimpleNamespace(tenant_store=ts, tenancy_token_map={})
    app.add_middleware(TenantMiddleware, container=container)
    @app.get("/who")
    def who(request: Request):
        t = getattr(request.state, "tenant", None)
        return {"tenant": t.tenant_id if t else None}
    client = TestClient(app)
    r = client.get("/who", headers={"X-Tenant-ID":"h1"})
    assert r.json()["tenant"] == "h1"
    r2 = client.get("/who", headers={"Host":"h1.localhost"})
    assert r2.json()["tenant"] == "h1"
