import time
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage

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
