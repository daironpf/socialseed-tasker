"""Solution similarity search and embedding backfill endpoints (issue #534)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.domain.entities import Component, Issue
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import ai_search

_UNIT_DIR = Path(__file__).resolve().parent


class FakeEmbedder:
    """Deterministic embedding port that records every text it receives."""

    def __init__(self, vector: list[float] | None = None) -> None:
        self.vector = [0.5] * 4 if vector is None else vector
        self.texts: list[str] = []

    def embed_text(self, text: str) -> list[float]:
        self.texts.append(text)
        return self.vector

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]


@pytest.fixture()
def repo():
    if str(_UNIT_DIR) not in sys.path:
        sys.path.insert(0, str(_UNIT_DIR))
    from test_api import MockRepository

    class VectorMockRepository(MockRepository):
        def __init__(self) -> None:
            super().__init__()
            self.embeddings: dict[str, list[float]] = {}
            self.search_results: list[dict] = []

        def update_issue_embedding(self, issue_id: str, embedding: list[float]) -> None:
            self.embeddings[issue_id] = embedding
            issue = self._issues.get(issue_id)
            if issue is not None:
                self._issues[issue_id] = issue.model_copy(update={"description_embedding": embedding})

        def search_by_embedding(self, embedding: list[float], threshold: float = 0.7, limit: int = 10) -> list[dict]:
            return self.search_results[:limit]

    return VectorMockRepository()


@pytest.fixture()
def client(repo):
    return TestClient(create_app(repository=repo))


@pytest.fixture()
def seeded(repo):
    component = repo.create_component(Component(name="Backend", project="proj"))
    closed = repo.create_issue(
        Issue(title="Closed fix", description="How it was solved", component_id=component.id)
    )
    open_issue = repo.create_issue(Issue(title="Open work", component_id=component.id))
    repo.close_issue(str(closed.id))
    repo.update_issue(str(closed.id), {"resolution": "implemented"})
    repo.search_results = [
        {"issue_id": str(closed.id), "title": "Closed fix", "score": 0.91},
        {"issue_id": str(open_issue.id), "title": "Open work", "score": 0.88},
    ]
    return closed, open_issue


def test_search_returns_only_closed_solutions(client, seeded, monkeypatch):
    closed, _ = seeded
    embedder = FakeEmbedder()
    monkeypatch.setattr(ai_search, "resolve_embedding_port", lambda: embedder)

    resp = client.post("/api/v1/ai/search-similar-solutions", json={"query": "timeout fix"})

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 1
    assert data[0]["issue_id"] == str(closed.id)
    assert data[0]["title"] == "Closed fix"
    assert data[0]["score"] == 0.91
    assert data[0]["resolution"] == "implemented"
    assert embedder.texts == ["timeout fix"]


def test_search_respects_limit(client, repo, monkeypatch):
    component = repo.create_component(Component(name="Backend", project="proj"))
    ids = []
    repo.search_results = []
    for index in range(3):
        issue = repo.create_issue(Issue(title=f"Fix {index}", component_id=component.id))
        repo.close_issue(str(issue.id))
        ids.append(str(issue.id))
        repo.search_results.append({"issue_id": str(issue.id), "title": f"Fix {index}", "score": 0.9})
    monkeypatch.setattr(ai_search, "resolve_embedding_port", lambda: FakeEmbedder())

    resp = client.post("/api/v1/ai/search-similar-solutions", json={"query": "fix", "limit": 2})

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert [item["issue_id"] for item in data] == ids[:2]


def test_search_without_provider_returns_empty(client, seeded, monkeypatch):
    monkeypatch.setattr(ai_search, "resolve_embedding_port", lambda: None)

    resp = client.post("/api/v1/ai/search-similar-solutions", json={"query": "anything"})

    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_search_requires_query(client):
    resp = client.post("/api/v1/ai/search-similar-solutions", json={})

    assert resp.status_code == 422


def test_backfill_embeds_missing_only(client, repo, monkeypatch):
    component = repo.create_component(Component(name="Backend", project="proj"))
    with_embedding = repo.create_issue(
        Issue(title="Already embedded", component_id=component.id, description_embedding=[0.9, 0.8])
    )
    missing = repo.create_issue(Issue(title="Missing embedding", component_id=component.id))
    repo.create_issue(Issue(title="Still open", component_id=component.id))
    repo.close_issue(str(with_embedding.id))
    repo.close_issue(str(missing.id))
    embedder = FakeEmbedder()
    monkeypatch.setattr(ai_search, "resolve_embedding_port", lambda: embedder)

    resp = client.post("/api/v1/ai/backfill-embeddings")

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data == {"embedded": 1, "skipped": 1, "failed": 0, "total_closed": 2}
    assert str(missing.id) in repo.embeddings
    assert str(with_embedding.id) not in repo.embeddings
    assert len(embedder.texts) == 1


def test_backfill_force_reembeds_everything(client, repo, monkeypatch):
    component = repo.create_component(Component(name="Backend", project="proj"))
    first = repo.create_issue(
        Issue(title="One", component_id=component.id, description_embedding=[0.9, 0.8])
    )
    second = repo.create_issue(Issue(title="Two", component_id=component.id))
    repo.close_issue(str(first.id))
    repo.close_issue(str(second.id))
    monkeypatch.setattr(ai_search, "resolve_embedding_port", lambda: FakeEmbedder())

    resp = client.post("/api/v1/ai/backfill-embeddings", params={"force": "true"})

    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data == {"embedded": 2, "skipped": 0, "failed": 0, "total_closed": 2}


def test_backfill_without_provider_returns_zero(client, seeded, monkeypatch):
    monkeypatch.setattr(ai_search, "resolve_embedding_port", lambda: None)

    resp = client.post("/api/v1/ai/backfill-embeddings")

    assert resp.status_code == 200
    assert resp.json()["data"] == {"embedded": 0, "skipped": 0, "failed": 0, "total_closed": 0}
