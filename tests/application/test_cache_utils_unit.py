from socialseed_tasker.application.cache_utils import get_or_set, memoize
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage

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
