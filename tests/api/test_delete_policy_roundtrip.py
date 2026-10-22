"""DELETE /policies/{id} roundtrip (issue #588).

The handler filtered the in-memory ``_policy_engine`` dict (always empty:
nothing populates it via the API) and returned 200 unconditionally, while
``list_policies`` reads Neo4j -> the policy never actually disappeared.
Fixed by deleting against Neo4j with existence check (404) and driver
guard (503). ``get_policy`` was also reading the dead in-memory dict
(always 404) and now reads Neo4j, so the delete is observable via
GET /policies/{id} as well.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.neo4j_repository import Neo4jTaskRepository
from socialseed_tasker.infrastructure.web_api.app import create_app


class _FakeResult:
    def __init__(self, records: list[dict[str, Any]] | None = None) -> None:
        self._records = records or []

    def single(self) -> dict[str, Any] | None:
        return self._records[0] if self._records else None

    def __iter__(self):
        return iter(self._records)


class _PolicySession:
    """Minimal Cypher emulation for Policy + RAG embedding queries."""

    def __init__(
        self,
        store: dict[str, dict[str, Any]],
        rag_store: list[dict[str, Any]],
        calls: list[tuple[str, dict[str, Any]]],
    ) -> None:
        self._store = store
        self._rag = rag_store
        self._calls = calls

    def run(
        self,
        query: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> _FakeResult:
        q = " ".join(query.split())
        p: dict[str, Any] = {**(params or {}), **kwargs}
        self._calls.append((q, p))

        if q.startswith("CREATE (p:Policy {"):
            node = dict(p)
            self._store[p["id"]] = node
            return _FakeResult([{"p": dict(node)}])

        if "SET n.embedding = $embedding" in q:
            node = self._store.get(p["id"])
            if node is None:
                return _FakeResult()
            node["embedding"] = p["embedding"]
            return _FakeResult([{"id": p["id"]}])

        if q.startswith("MATCH (p:Policy {id: $id}) DETACH DELETE p"):
            self._store.pop(p["id"], None)
            return _FakeResult()

        if q.startswith("MATCH (p:Policy {id: $id})"):
            node = self._store.get(p["id"])
            return _FakeResult([{"p": dict(node)}]) if node else _FakeResult()

        if q.startswith("MATCH (p:Policy {name: $name})"):
            for node in self._store.values():
                if node.get("name") == p["name"]:
                    return _FakeResult([{"p": dict(node)}])
            return _FakeResult()

        if q.startswith("MATCH (p:Policy)"):
            return _FakeResult([{"p": dict(n)} for n in self._store.values()])

        if q.startswith("MATCH (e:RAGEmbedding {sourceType: $source_type, sourceId: $source_id})"):
            self._rag[:] = [
                e
                for e in self._rag
                if not (e["sourceType"] == p["source_type"] and e["sourceId"] == p["source_id"])
            ]
            return _FakeResult()

        return _FakeResult()

    def __enter__(self) -> _PolicySession:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _InnerDriver:
    def __init__(
        self,
        store: dict[str, dict[str, Any]],
        rag_store: list[dict[str, Any]],
        calls: list[tuple[str, dict[str, Any]]],
    ) -> None:
        self._store = store
        self._rag = rag_store
        self._calls = calls

    def session(self, database: str | None = None) -> _PolicySession:
        return _PolicySession(self._store, self._rag, self._calls)


class _OuterDriver:
    def __init__(self) -> None:
        self.store: dict[str, dict[str, Any]] = {}
        self.rag_store: list[dict[str, Any]] = []
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.driver = _InnerDriver(self.store, self.rag_store, self.calls)
        self.database = "neo4j"
        self.uri = "bolt://fake:7687"

    def health_check(self) -> bool:
        return True


def _make_client(
    monkeypatch: pytest.MonkeyPatch,
    driver: _OuterDriver | None = None,
    with_driver: bool = True,
) -> tuple[TestClient, _OuterDriver]:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    outer = driver or _OuterDriver()
    repo = Neo4jTaskRepository(outer)
    app = create_app(repository=repo, neo4j_driver=outer if with_driver else None)
    return TestClient(app), outer


def _create_policy(client: TestClient, name: str = "No cycles") -> str:
    resp = client.post(
        "/api/v1/policies",
        json={
            "name": name,
            "description": "frontend never depends on backend",
            "rules": [
                {
                    "rule_type": "forbidden_label_dependency",
                    "from_pattern": "frontend",
                    "to_pattern": "backend",
                }
            ],
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]["id"]


def test_delete_policy_roundtrip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, driver = _make_client(monkeypatch)
    policy_id = _create_policy(client)

    resp = client.get(f"/api/v1/policies/{policy_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["name"] == "No cycles"
    assert policy_id in driver.store

    resp = client.delete(f"/api/v1/policies/{policy_id}")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == {"deleted": policy_id}

    assert policy_id not in driver.store, "policy node must be gone from Neo4j"

    resp = client.get("/api/v1/policies")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == []

    resp = client.get(f"/api/v1/policies/{policy_id}")
    assert resp.status_code == 404, resp.text


def test_delete_unknown_policy_returns_404(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = _make_client(monkeypatch)

    resp = client.delete("/api/v1/policies/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404, resp.text


def test_delete_policy_cleans_rag_embedding_nodes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, driver = _make_client(monkeypatch)
    policy_id = _create_policy(client, name="Ragged policy")

    driver.rag_store.append(
        {"id": "emb-1", "sourceType": "policy", "sourceId": policy_id, "content": "x"}
    )

    resp = client.delete(f"/api/v1/policies/{policy_id}")
    assert resp.status_code == 200, resp.text
    assert driver.rag_store == [], "RAGEmbedding nodes for the policy must be cleaned"


def test_delete_policy_503_without_driver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _ = _make_client(monkeypatch, with_driver=False)

    resp = client.delete("/api/v1/policies/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 503, resp.text
