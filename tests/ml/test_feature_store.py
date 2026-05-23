from socialseed_tasker.ml.feature_store import FeatureStore
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage


def test_put_get_list():
    s = MemoryStorage()
    fs = FeatureStore(s)
    fs.put_features("k1", {"a": 1})
    assert fs.get_features("k1") == {"a": 1}
    assert "k1" in fs.list_keys()


def test_get_nonexistent():
    s = MemoryStorage()
    fs = FeatureStore(s)
    assert fs.get_features("nonexistent") is None


def test_list_prefix():
    s = MemoryStorage()
    fs = FeatureStore(s)
    fs.put_features("user:1", {"x": 1})
    fs.put_features("user:2", {"y": 2})
    fs.put_features("global", {"z": 3})
    assert sorted(fs.list_keys("user:")) == ["user:1", "user:2"]


def test_compute_input_hash():
    s = MemoryStorage()
    fs = FeatureStore(s)
    h1 = fs.compute_input_hash({"a": 1, "b": 2})
    h2 = fs.compute_input_hash({"b": 2, "a": 1})
    assert h1 == h2
