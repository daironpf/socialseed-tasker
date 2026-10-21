"""POST /commits roundtrip (issue #584).

``create_commit`` read camelCase attributes (``commit.authorName``) off the
snake_case ``Commit`` entity -> 500 on every commit write; the same latent bug
lived in ``_commit_to_response`` (used by POST and both GETs). These tests pin
the query kwargs contract and a full API roundtrip.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from fastapi.testclient import TestClient

from socialseed_tasker.domain.entities import Commit
from socialseed_tasker.infrastructure.neo4j_commit_repository import CommitRepository
from socialseed_tasker.infrastructure.web_api.app import create_app


class _FakeResult:
    def __init__(self, records: list[dict[str, Any]] | None = None) -> None:
        self._records = records or []

    def single(self) -> dict[str, Any] | None:
        return self._records[0] if self._records else None

    def __iter__(self):
        return iter(self._records)


# ---------------------------------------------------------------------------
# Recording driver: captures session.run(query, **params)
# ---------------------------------------------------------------------------


class _RecordingSession:
    def __init__(self, driver: _RecordingDriver) -> None:
        self._driver = driver

    def run(self, query: str, **params: Any) -> _FakeResult:
        self._driver.calls.append((query, params))
        return _FakeResult()

    def __enter__(self) -> _RecordingSession:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _RecordingDriver:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def session(self, database: str | None = None) -> _RecordingSession:
        return _RecordingSession(self)


def test_create_commit_sends_snake_case_query_params() -> None:
    repo = CommitRepository(_RecordingDriver())
    commit = Commit(
        sha="a" * 40,
        message="feat: thing",
        author_name="Ana",
        author_email="ana@example.com",
        is_ai_generated=True,
        branch="main",
        additions=10,
        deletions=2,
        files_changed=3,
    )

    repo.create_commit(commit)

    assert len(repo._driver.calls) == 1
    query, params = repo._driver.calls[0]
    assert "authorName: $author_name" in query
    assert "authorEmail: $author_email" in query
    assert "isAiGenerated: $is_ai_generated" in query
    assert "filesChanged: $files_changed" in query
    assert params == {
        "sha": "a" * 40,
        "message": "feat: thing",
        "author_name": "Ana",
        "author_email": "ana@example.com",
        "timestamp": commit.timestamp.isoformat(),
        "is_ai_generated": True,
        "branch": "main",
        "additions": 10,
        "deletions": 2,
        "files_changed": 3,
    }


# ---------------------------------------------------------------------------
# API roundtrip through a commit-aware fake driver
# ---------------------------------------------------------------------------


class _CommitSession:
    """Minimal Cypher emulation for CREATE/GET/LIST/DELETE of Commit nodes."""

    def __init__(self, store: dict[str, dict[str, Any]]) -> None:
        self._store = store

    def run(self, query: str, **params: Any) -> _FakeResult:
        q = " ".join(query.split()).lower()
        if q.startswith("match (c:commit {sha: $sha}) detach delete"):
            self._store.pop(params["sha"], None)
            return _FakeResult()
        if q.startswith("match (c:commit {sha: $sha})"):
            node = self._store.get(params["sha"])
            return _FakeResult([{"c": node}]) if node else _FakeResult()
        if q.startswith("match (c:commit)"):
            return _FakeResult([{"c": n} for n in self._store.values()])
        if q.startswith("create (c:commit"):
            node = {
                "sha": params["sha"],
                "message": params["message"],
                "authorName": params["author_name"],
                "authorEmail": params["author_email"],
                "timestamp": params["timestamp"],
                "isAiGenerated": params["is_ai_generated"],
                "branch": params["branch"],
                "additions": params["additions"],
                "deletions": params["deletions"],
                "filesChanged": params["files_changed"],
            }
            self._store[params["sha"]] = node
            return _FakeResult([{"c": node}])
        return _FakeResult()

    def __enter__(self) -> _CommitSession:
        return self

    def __exit__(self, *args: Any) -> bool:
        return False


class _InnerDriver:
    def __init__(self, store: dict[str, dict[str, Any]]) -> None:
        self._store = store

    def session(self, database: str | None = None) -> _CommitSession:
        return _CommitSession(self._store)


class _OuterDriver:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self.driver = _InnerDriver(self._store)
        self.database = "neo4j"
        self.uri = "bolt://fake:7687"

    def health_check(self) -> bool:
        return True


def test_post_commit_roundtrip_via_api() -> None:
    driver = _OuterDriver()
    client = TestClient(create_app(repository=None, neo4j_driver=driver))
    sha = "f" * 40
    body = {
        "sha": sha,
        "message": "fix: thing",
        "author_name": "Ana",
        "author_email": "ana@example.com",
        "is_ai_generated": False,
        "branch": "main",
        "additions": 7,
        "deletions": 1,
        "files_changed": 2,
    }

    resp = client.post("/api/v1/commits", json=body)
    assert resp.status_code in (200, 201), resp.text
    created = resp.json()["data"]
    assert created["sha"] == sha
    assert created["author_name"] == "Ana"

    resp = client.get(f"/api/v1/commits/{sha}")
    assert resp.status_code == 200, resp.text
    fetched = resp.json()["data"]
    assert fetched["message"] == "fix: thing"
    assert fetched["author_name"] == "Ana"
    assert fetched["author_email"] == "ana@example.com"
    assert fetched["files_changed"] == 2

    resp = client.get("/api/v1/commits")
    assert resp.status_code == 200
    listed = resp.json()["data"]
    assert [c["sha"] for c in listed] == [sha]

    resp = client.delete(f"/api/v1/commits/{sha}")
    assert resp.status_code in (200, 204), resp.text
    resp = client.get(f"/api/v1/commits/{sha}")
    assert resp.status_code == 404


def test_get_unknown_commit_returns_404() -> None:
    driver = _OuterDriver()
    client = TestClient(create_app(repository=None, neo4j_driver=driver))

    resp = client.get(f"/api/v1/commits/{'0' * 40}")

    assert resp.status_code == 404
