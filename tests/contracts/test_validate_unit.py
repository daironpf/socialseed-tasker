from tools.contracts.validator import validate_response


def test_validate_simple_ok():
    schema = {"type": "object", "properties": {"a": {"type": "integer"}}}
    resp = {"a": 1}
    r = validate_response(schema, resp)
    assert r["ok"]


def test_validate_simple_fail():
    schema = {"type": "object", "properties": {"a": {"type": "integer"}}}
    resp = {"a": "x"}
    r = validate_response(schema, resp)
    assert not r["ok"]


def test_validate_none_schema():
    r = validate_response(None, {"a": 1})
    assert r["ok"]


def test_validate_nested_object():
    schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
                "required": ["name", "age"],
            }
        },
        "required": ["user"],
    }
    resp = {"user": {"name": "Alice", "age": 30}}
    r = validate_response(schema, resp)
    assert r["ok"]


def test_validate_nested_object_fail():
    schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"},
                },
                "required": ["name", "age"],
            }
        },
        "required": ["user"],
    }
    resp = {"user": {"name": "Alice", "age": "thirty"}}
    r = validate_response(schema, resp)
    assert not r["ok"]


def test_validate_array():
    schema = {
        "type": "array",
        "items": {"type": "integer"},
    }
    resp = [1, 2, 3]
    r = validate_response(schema, resp)
    assert r["ok"]


def test_validate_array_fail():
    schema = {
        "type": "array",
        "items": {"type": "integer"},
    }
    resp = [1, "x", 3]
    r = validate_response(schema, resp)
    assert not r["ok"]
