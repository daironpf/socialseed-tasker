# tests/tenancy/test_tenant_store_unit.py
from socialseed_tasker.tenancy.store import TenantStore
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage

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
