from socialseed_tasker.data_catalog.registry import SchemaRegistry, SchemaCompatibilityError
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage


def test_backward_compatibility_rejects_missing_field():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    v1 = {"type": "object", "properties": {"a": {"type": "integer"}}}
    reg.register_schema("s2", "1.0.0", v1)
    v2 = {"type": "object", "properties": {}}
    try:
        reg.register_schema("s2", "1.1.0", v2, compatibility="BACKWARD")
        assert False, "should have raised"
    except SchemaCompatibilityError:
        assert True


def test_backward_compatibility_accepts_new_field():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    v1 = {"type": "object", "properties": {"a": {"type": "integer"}}}
    reg.register_schema("s3", "1.0.0", v1)
    v2 = {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "string"}}}
    reg.register_schema("s3", "1.1.0", v2, compatibility="BACKWARD")
    assert reg.get_versions("s3") == ["1.0.0", "1.1.0"]


def test_forward_compatibility_rejects_new_field():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    v1 = {"type": "object", "properties": {"a": {"type": "integer"}}}
    reg.register_schema("s4", "1.0.0", v1)
    v2 = {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "string"}}}
    try:
        reg.register_schema("s4", "1.1.0", v2, compatibility="FORWARD")
        assert False, "should have raised"
    except SchemaCompatibilityError:
        assert True


def test_full_compatibility():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    v1 = {"type": "object", "properties": {"a": {"type": "integer"}}}
    reg.register_schema("s5", "1.0.0", v1)
    v2 = {"type": "object", "properties": {"a": {"type": "integer"}}}
    reg.register_schema("s5", "1.1.0", v2, compatibility="FULL")
    assert len(reg.get_versions("s5")) == 2


def test_none_compatibility_always_passes():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    v1 = {"type": "object", "properties": {"a": {"type": "integer"}}}
    reg.register_schema("s6", "1.0.0", v1)
    v2 = {"type": "object", "properties": {}}  # removes field
    reg.register_schema("s6", "1.1.0", v2, compatibility="NONE")
    assert len(reg.get_versions("s6")) == 2


def test_first_version_no_compatibility_check():
    s = MemoryStorage()
    reg = SchemaRegistry(s)
    reg.register_schema("s7", "1.0.0", {"type": "object", "properties": {}})
    assert reg.get_versions("s7") == ["1.0.0"]
