import os
import pytest
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.data_catalog.registry import SchemaRegistry

pytestmark = pytest.mark.integration


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_registry_roundtrip():
    _skip_if_not_integration()
    storage = MemoryStorage()
    reg = SchemaRegistry(storage)
    schema = {"type": "object", "properties": {"x": {"type": "integer"}}}
    reg.register_schema("inttest", "1.0.0", schema)
    assert reg.get_schema("inttest", "1.0.0")["properties"]["x"]["type"] == "integer"
    reg.register_dataset("int_ds", "Integration DS", "Test", "inttest", "1.0.0", "tester")
    ds = reg.get_dataset("int_ds")
    assert ds["title"] == "Integration DS"
