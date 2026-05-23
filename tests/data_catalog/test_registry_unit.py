import json
from socialseed_tasker.data_catalog.registry import SchemaRegistry, SchemaCompatibilityError
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage


def test_register_and_get_schema():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    schema_v1 = {"type": "object", "properties": {"a": {"type": "integer"}}}
    reg.register_schema("s1", "1.0.0", schema_v1)
    assert reg.get_schema("s1", "1.0.0")["properties"]["a"]["type"] == "integer"
    assert reg.get_versions("s1") == ["1.0.0"]


def test_register_schema_invalid_version():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    try:
        reg.register_schema("bad", "abc", {})
        assert False, "should have raised"
    except ValueError:
        assert True


def test_get_nonexistent_schema():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    try:
        reg.get_schema("nonexistent", "1.0.0")
        assert False, "should have raised"
    except KeyError:
        assert True


def test_register_and_get_dataset():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    schema_v1 = {"type": "object", "properties": {"x": {"type": "string"}}}
    reg.register_schema("ds_schema", "1.0.0", schema_v1)
    reg.register_dataset("ds1", "Dataset 1", "A test dataset", "ds_schema", "1.0.0", "owner1", tags=["test"])
    d = reg.get_dataset("ds1")
    assert d["title"] == "Dataset 1"
    assert d["owner"] == "owner1"
    assert "test" in d["tags"]


def test_list_datasets():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    reg.register_dataset("ds1", "DS1", "", "s1", "1.0.0", "o1")
    reg.register_dataset("ds2", "DS2", "", "s1", "1.0.0", "o2")
    datasets = reg.list_datasets()
    assert len(datasets) == 2
    assert {d["dataset_id"] for d in datasets} == {"ds1", "ds2"}


def test_get_nonexistent_dataset():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    try:
        reg.get_dataset("nonexistent")
        assert False, "should have raised"
    except KeyError:
        assert True


def test_list_schemas():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    reg.register_schema("s1", "1.0.0", {"type": "object"})
    reg.register_schema("s1", "1.1.0", {"type": "object", "properties": {"a": {"type": "integer"}}})
    reg.register_schema("s2", "1.0.0", {"type": "object"})
    schemas = reg.list_schemas()
    names = {sc["name"] for sc in schemas}
    assert "s1" in names
    assert "s2" in names
