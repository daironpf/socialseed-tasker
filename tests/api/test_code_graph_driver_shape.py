"""Issues #582/#583: code-graph endpoints with both driver shapes.

#582 — ``/code-graph/files`` and ``/code-graph/symbols`` never declared the
driver dependency, so any invocation raised ``NameError: name 'driver' is not
defined`` → 500. They must now behave like the rest of the router: 200 with the
``Neo4j not connected`` guard when there is no driver, 200 with data otherwise.

#583 — ``retrieve_neo4j_code_graph_driver`` unwraps ``app.state.driver`` and
hands the repository a **raw** Bolt driver, but ``_session()`` assumed a
wrapper (``.driver``/``.database``) → ``AttributeError: 'BoltDriver' object has
no attribute 'driver'`` → 500 on every code-graph endpoint with a real
connection. These tests feed a wrapper that unwraps to a raw driver (the
production shape) and require 200s.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app

# One record carrying every key any code-graph query might read, so the same
# fake result serves get_files (``f``), find_symbols (``s``) and get_stats.
_RECORD: dict[str, Any] = {
    "f": {
        "id": "file-1",
        "name": "app.py",
        "path": "src/app.py",
        "language": "python",
        "lines_of_code": 10,
    },
    "s": {
        "id": "sym-1",
        "name": "main",
        "symbol_type": "FUNCTION",
        "start_line": 1,
        "end_line": 5,
        "path": "src/app.py",
    },
    "file_path": "src/app.py",
    "total_files": 1,
    "total_symbols": 1,
    "total_relationships": 0,
}


class _GraphResult:
    def __init__(self) -> None:
        self._records = [_RECORD]

    def single(self) -> dict[str, Any] | None:
        return self._records[0]

    def __iter__(self):
        return iter(self._records)


class _RawSession:
    def run(self, query: str, *args: Any, **kwargs: Any) -> _GraphResult:
        return _GraphResult()

    def __enter__(self) -> _RawSession:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _RawDriver:
    """Raw Bolt-style driver: has ``.session()`` but no ``.driver``/``.database``."""

    def __init__(self) -> None:
        self.databases: list[str] = []

    def session(self, database: str | None = None) -> _RawSession:
        self.databases.append(database or "")
        return _RawSession()


class _Wrapper:
    """App-state wrapper shape: exposes ``.driver`` and ``.database``."""

    def __init__(self, inner: _RawDriver, database: str = "neo4j") -> None:
        self.driver = inner
        self.database = database


class _MinimalRepository:
    def __init__(self, raw: _RawDriver | None = None) -> None:
        self.raw = raw


def _client(neo4j_driver: Any) -> TestClient:
    app = create_app(repository=_MinimalRepository(), neo4j_driver=neo4j_driver)
    return TestClient(app)


def test_files_without_driver_returns_guard_not_nameerror() -> None:
    resp = _client(None).get("/api/v1/code-graph/files")
    assert resp.status_code == 200, resp.text[:300]
    assert resp.json()["error"] == "Neo4j not connected"


def test_symbols_without_driver_returns_guard_not_nameerror() -> None:
    resp = _client(None).get("/api/v1/code-graph/symbols")
    assert resp.status_code == 200, resp.text[:300]
    assert resp.json()["error"] == "Neo4j not connected"


def test_files_with_raw_driver_returns_200() -> None:
    raw = _RawDriver()
    client = _client(_Wrapper(raw))
    resp = client.get("/api/v1/code-graph/files")
    assert resp.status_code == 200, resp.text[:300]
    body = resp.json()
    assert body["total"] == 1
    assert body["files"][0]["path"] == "src/app.py"
    assert raw.databases, "_session() never opened a session on the raw driver"


def test_symbols_with_raw_driver_returns_200() -> None:
    raw = _RawDriver()
    client = _client(_Wrapper(raw))
    resp = client.get("/api/v1/code-graph/symbols", params={"name": "main"})
    assert resp.status_code == 200, resp.text[:300]
    body = resp.json()
    assert body["total"] == 1
    assert body["symbols"][0]["name"] == "main"


def test_stats_with_raw_driver_returns_200() -> None:
    raw = _RawDriver()
    client = _client(_Wrapper(raw))
    resp = client.get("/api/v1/code-graph/stats")
    assert resp.status_code == 200, resp.text[:300]
    body = resp.json()
    assert body["total_files"] == 1
    assert body["total_symbols"] == 1
    assert body["total_relationships"] == 0


def test_raw_driver_passed_directly_also_works() -> None:
    raw = _RawDriver()
    client = _client(raw)
    resp = client.get("/api/v1/code-graph/files")
    assert resp.status_code == 200, resp.text[:300]
    assert raw.databases == ["neo4j"]
