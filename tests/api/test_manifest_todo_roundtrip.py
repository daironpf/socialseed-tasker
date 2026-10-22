"""PATCH /issues/{id}/manifest/todo roundtrip (issue #586).

The handler built a list of maps and stored it as a Neo4j node property ->
``CypherTypeError`` 500 (properties must be primitives or arrays thereof).
Fixed by serializing the list to a JSON string (``completed`` as a real bool,
never ``str(False)`` -> ``"False"``) and parsing symmetrically on read via
``_parse_manifest_todo``.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.neo4j_impl.shared import _parse_manifest_todo
from socialseed_tasker.infrastructure.neo4j_repository import Neo4jTaskRepository
from socialseed_tasker.infrastructure.web_api.app import create_app

ISSUE_ID = "11111111-1111-1111-1111-111111111111"


class _FakeResult:
    def __init__(self, records: list[dict[str, Any]] | None = None) -> None:
        self._records = records or []

    def single(self) -> dict[str, Any] | None:
        return self._records[0] if self._records else None

    def __iter__(self):
        return iter(self._records)


class _IssueSession:
    """Minimal Cypher emulation for GET_ISSUE / UPDATE_ISSUE."""

    def __init__(self, store: dict[str, dict[str, Any]], calls: list[tuple[str, dict[str, Any]]]) -> None:
        self._store = store
        self._calls = calls

    def run(self, query: str, **params: Any) -> _FakeResult:
        q = " ".join(query.split())
        self._calls.append((q, params))
        if q.startswith("MATCH (i:Issue {id: $id}) SET i +="):
            node = self._store.get(params["id"])
            if node is None:
                return _FakeResult()
            node.update(params["updates"])
            node["updatedAt"] = params["updated_at"]
            return _FakeResult([{"i": dict(node)}])
        if q.startswith("MATCH (i:Issue {id: $id})"):
            node = self._store.get(params["id"])
            return _FakeResult([{"i": dict(node)}]) if node else _FakeResult()
        return _FakeResult()

    def __enter__(self) -> _IssueSession:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _InnerDriver:
    def __init__(self, store: dict[str, dict[str, Any]], calls: list[tuple[str, dict[str, Any]]]) -> None:
        self._store = store
        self._calls = calls

    def session(self, database: str | None = None) -> _IssueSession:
        return _IssueSession(self._store, self._calls)


class _OuterDriver:
    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {
            ISSUE_ID: {
                "id": ISSUE_ID,
                "title": "Manifest issue",
                "status": "OPEN",
                "priority": "MEDIUM",
                "manifestTodo": [],
                "manifestFiles": [],
                "manifestNotes": [],
            }
        }
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.driver = _InnerDriver(self.store, self.calls)
        self.database = "neo4j"
        self.uri = "bolt://fake:7687"

    def health_check(self) -> bool:
        return True


def _make_client() -> tuple[TestClient, _OuterDriver]:
    driver = _OuterDriver()
    repo = Neo4jTaskRepository(driver)
    return TestClient(create_app(repository=repo, neo4j_driver=driver)), driver


def test_patch_manifest_todo_roundtrip() -> None:
    client, driver = _make_client()
    items = [
        {"task": "t1", "completed": False},
        {"task": "t2", "completed": True},
    ]

    resp = client.patch(f"/api/v1/issues/{ISSUE_ID}/manifest/todo", json={"todo": items})
    assert resp.status_code == 200, resp.text
    returned = resp.json()["data"]["manifest_todo"]
    assert returned == items
    assert returned[0]["completed"] is False
    assert returned[1]["completed"] is True

    stored = driver.store[ISSUE_ID]["manifestTodo"]
    assert isinstance(stored, str), "manifestTodo must be a primitive (JSON string), never a map/list"
    assert json.loads(stored) == items

    resp = client.get(f"/api/v1/issues/{ISSUE_ID}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["manifest_todo"] == items

    resp = client.get(f"/api/v1/issues/{ISSUE_ID}/manifest")
    assert resp.status_code == 200, resp.text
    manifest = resp.json()["data"]
    assert manifest["todo"] == items
    assert manifest["todo"][0]["completed"] is False


def test_patch_manifest_todo_completed_true_stays_bool() -> None:
    client, driver = _make_client()

    resp = client.patch(
        f"/api/v1/issues/{ISSUE_ID}/manifest/todo",
        json={"todo": [{"task": "only", "completed": True}]},
    )
    assert resp.status_code == 200, resp.text
    completed = resp.json()["data"]["manifest_todo"][0]["completed"]
    assert type(completed) is bool
    assert completed is True

    stored = json.loads(driver.store[ISSUE_ID]["manifestTodo"])
    assert type(stored[0]["completed"]) is bool
    assert stored[0]["completed"] is True


def test_patch_manifest_todo_unknown_issue_returns_404() -> None:
    client, _ = _make_client()

    resp = client.patch(
        "/api/v1/issues/00000000-0000-0000-0000-000000000000/manifest/todo",
        json={"todo": [{"task": "t1", "completed": False}]},
    )
    assert resp.status_code == 404


def test_parse_manifest_todo_variants() -> None:
    items = [{"task": "t1", "completed": False}]
    assert _parse_manifest_todo(json.dumps(items)) == items
    assert _parse_manifest_todo(items) == items
    assert _parse_manifest_todo(None) == []
    assert _parse_manifest_todo("not-json") == []
    assert _parse_manifest_todo('"just a string"') == []
    assert _parse_manifest_todo(["legacy", {"task": "kept", "completed": True}]) == [
        {"task": "kept", "completed": True}
    ]
