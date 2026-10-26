"""POST /ai/issues/{id}/embed degradation (issue #590).

The handler raised ``HTTPException(400, "OPENAI_API_KEY not configured")``
INSIDE a ``try`` whose ``except Exception`` re-wrapped it as
``500 {"detail": "400: OPENAI_API_KEY not configured"}`` — wrong status,
``{"detail": ...}`` instead of the standard ``{data, error, meta}`` envelope
and a mixed-level message. The same wrapping masked the unknown-issue 404 as
``500 "404: Issue not found"``.

Fixed: key absence raises ``AIServiceNotConfiguredError`` handled app-wide as
``503 AI_NOT_CONFIGURED`` (envelope); unexpected errors propagate to
``generic_error_handler`` (``INTERNAL_ERROR`` envelope + logging, issue #594);
the 404 stays a 404. Neighbors (``search-context``, ``search-similar-solutions``,
``backfill-embeddings``) already degrade explicitly to empty/zero results
without a 500 path (covered by their own tests).
"""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app

FAKE_KEY = "sk-test-fake-openai-key-for-unit-tests"


class _IssueStub:
    def __init__(self, embedding: list[float] | None = None) -> None:
        self.description_embedding = embedding
        self.description = "issue description"
        self.title = "issue title"


class _Repo:
    def __init__(self, issue: Any = None) -> None:
        self.issue = issue
        self.updated: tuple[str, list[float]] | None = None
        self.explode = False

    def get_issue(self, issue_id: str) -> Any:
        if self.explode:
            raise RuntimeError("repo exploded")
        return self.issue if self.issue is not None else None

    def update_issue_embedding(self, issue_id: str, embedding: list[float]) -> None:
        self.updated = (issue_id, embedding)


def _client(repo: Any, raise_server_exceptions: bool = True) -> TestClient:
    return TestClient(
        create_app(repository=repo, neo4j_driver=None),
        raise_server_exceptions=raise_server_exceptions,
    )


def test_embed_without_openai_key_returns_503_with_envelope(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = _client(_Repo(_IssueStub()))

    resp = client.post("/api/v1/ai/issues/known/embed")
    assert resp.status_code == 503, resp.text
    body = resp.json()
    assert body["data"] is None
    assert body["error"]["code"] == "AI_NOT_CONFIGURED"
    assert "OPENAI_API_KEY" in body["error"]["message"]
    assert body["meta"]["request_id"]
    assert "400:" not in resp.text


def test_embed_unknown_issue_returns_404_not_500(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    client = _client(_Repo(None))

    resp = client.post("/api/v1/ai/issues/nonexistent/embed")
    assert resp.status_code == 404, resp.text
    body = resp.json()
    assert body["data"] is None
    assert body["error"]["code"] == "NOT_FOUND"
    assert body["error"]["message"] == "Issue not found"
    assert body["meta"]["request_id"]


def test_embed_with_key_and_existing_embedding_short_circuits(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    repo = _Repo(_IssueStub(embedding=[0.1, 0.2]))
    client = _client(repo)

    resp = client.post("/api/v1/ai/issues/known/embed")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == {"issue_id": "known", "embedding_exists": True}
    assert repo.updated is None


def test_embed_unexpected_error_uses_api_error_envelope(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", FAKE_KEY)
    repo = _Repo(_IssueStub(embedding=None))
    repo.explode = True
    client = _client(repo, raise_server_exceptions=False)

    resp = client.post("/api/v1/ai/issues/known/embed")
    assert resp.status_code == 500, resp.text
    body = resp.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["data"] is None
    assert body["meta"]["request_id"]
