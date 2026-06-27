# tests/integration/test_tenant_isolation.py
import os
import pytest
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.infrastructure.tenant_storage import NamespacedStorage
from socialseed_tasker.tenancy.store import TenantStore

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
