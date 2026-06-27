import json
import time

import pytest
import requests

from tools.contracts.mock_server import MockServer


def _wait_for_server(url: str, timeout: float = 3.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            r = requests.get(url, timeout=1)
            if r.status_code < 500:
                return
        except requests.ConnectionError:
            time.sleep(0.1)
    raise TimeoutError(f"Server at {url} did not start within {timeout}s")


def test_mock_server_start(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/ping": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "pong": {"type": "string"}
                                        },
                                    }
                                }
                            },
                        }
                    }
                }
            }
        },
    }
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec))
    ms = MockServer(spec_path=str(p), port=9010, seed=123)
    ms.start()
    _wait_for_server("http://localhost:9010/ping")
    r = requests.get("http://localhost:9010/ping", timeout=2)
    assert r.status_code == 200
    j = r.json()
    assert "pong" in j


def test_mock_server_deterministic(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/items": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "integer"},
                                            "name": {"type": "string"},
                                        },
                                    }
                                }
                            },
                        }
                    }
                }
            }
        },
    }
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec))
    ms = MockServer(spec_path=str(p), port=9011, seed=42)
    ms.start()
    _wait_for_server("http://localhost:9011/items")
    r1 = requests.get("http://localhost:9011/items", timeout=2).json()
    ms2 = MockServer(spec_path=str(p), port=9012, seed=42)
    ms2.start()
    _wait_for_server("http://localhost:9012/items")
    r2 = requests.get("http://localhost:9012/items", timeout=2).json()
    assert r1 == r2


def test_mock_server_with_overrides(tmp_path):
    spec = {
        "openapi": "3.0.0",
        "paths": {
            "/custom": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "ok",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "value": {"type": "string"}
                                        },
                                    }
                                }
                            },
                        }
                    }
                }
            }
        },
    }
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(spec))
    overrides = tmp_path / "overrides"
    overrides.mkdir()
    override_file = overrides / "GET_custom.json"
    override_file.write_text(json.dumps({"value": "overridden"}))
    ms = MockServer(
        spec_path=str(p), port=9013, overrides_dir=str(overrides), seed=42
    )
    ms.start()
    _wait_for_server("http://localhost:9013/custom")
    r = requests.get("http://localhost:9013/custom", timeout=2).json()
    assert r == {"value": "overridden"}
