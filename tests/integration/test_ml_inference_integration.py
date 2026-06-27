import os
import pytest
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.ml.feature_store import FeatureStore

pytestmark = pytest.mark.integration


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_feature_store_roundtrip():
    _skip_if_not_integration()
    storage = MemoryStorage()
    fs = FeatureStore(storage)
    fs.put_features("demo", {"a": 1, "b": 2})
    assert fs.get_features("demo") == {"a": 1, "b": 2}
    assert "demo" in fs.list_keys()
