"""Close-time solution embedding: content, degradation and idempotency (issue #534)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from socialseed_tasker.application import actions as actions_module
from socialseed_tasker.application.actions import (
    IssueAlreadyClosedError,
    OpenDependenciesError,
    build_solution_text,
    close_issue_action,
    resolve_embedding_port,
)
from socialseed_tasker.domain.entities import Component, Issue, IssueStatus

_UNIT_DIR = Path(__file__).resolve().parent


class FakeEmbedder:
    """Deterministic embedding port that records every text it receives."""

    def __init__(self, vector: list[float] | None = None, error: Exception | None = None) -> None:
        self.vector = [0.1, 0.2, 0.3] if vector is None else vector
        self.error = error
        self.texts: list[str] = []

    def embed_text(self, text: str) -> list[float]:
        self.texts.append(text)
        if self.error is not None:
            raise self.error
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

        def close_issue(self, issue_id: str, commit_sha: str | None = None, resolution: str = "implemented") -> Issue:
            issue = self._issues[issue_id]
            updated = issue.model_copy(
                update={
                    "status": IssueStatus.CLOSED,
                    "resolution": resolution,
                    "resolved_by_commit_sha": commit_sha,
                }
            )
            self._issues[issue_id] = updated
            return updated

        def update_issue_embedding(self, issue_id: str, embedding: list[float]) -> None:
            self.embeddings[issue_id] = embedding

    return VectorMockRepository()


@pytest.fixture()
def issue(repo):
    component = repo.create_component(Component(name="Backend", project="proj"))
    return repo.create_issue(
        Issue(
            title="Fix auth timeout",
            description="Requests hang behind the proxy",
            component_id=component.id,
        )
    )


def test_close_embeds_solution_text(repo, issue):
    embedder = FakeEmbedder()

    closed = close_issue_action(
        repo,
        str(issue.id),
        commit_sha="abc123",
        resolution="implemented",
        embedder=embedder,
    )

    assert closed.status == IssueStatus.CLOSED
    assert repo.embeddings == {str(issue.id): [0.1, 0.2, 0.3]}
    assert len(embedder.texts) == 1
    text = embedder.texts[0]
    assert "Fix auth timeout" in text
    assert "implemented" in text
    assert "Requests hang behind the proxy" in text
    assert "abc123" in text


def test_close_continues_when_embedder_raises(repo, issue):
    embedder = FakeEmbedder(error=RuntimeError("provider down"))

    closed = close_issue_action(repo, str(issue.id), embedder=embedder)

    assert closed.status == IssueStatus.CLOSED
    assert repo.embeddings == {}


def test_close_without_provider_skips_embedding(repo, issue, monkeypatch):
    monkeypatch.setattr(actions_module, "resolve_embedding_port", lambda: None)

    closed = close_issue_action(repo, str(issue.id))

    assert closed.status == IssueStatus.CLOSED
    assert repo.embeddings == {}


def test_close_with_empty_embedding_does_not_store(repo, issue):
    embedder = FakeEmbedder(vector=[])

    closed = close_issue_action(repo, str(issue.id), embedder=embedder)

    assert closed.status == IssueStatus.CLOSED
    assert repo.embeddings == {}


def test_close_with_open_dependencies_does_not_embed(repo, issue):
    component = repo.create_component(Component(name="Frontend", project="proj"))
    dep = repo.create_issue(Issue(title="Pending dependency", component_id=component.id))
    repo.add_dependency(str(issue.id), str(dep.id))
    embedder = FakeEmbedder()

    with pytest.raises(OpenDependenciesError):
        close_issue_action(repo, str(issue.id), embedder=embedder)

    assert embedder.texts == []
    assert repo.embeddings == {}


def test_closing_twice_does_not_reembed(repo, issue):
    first = FakeEmbedder()
    close_issue_action(repo, str(issue.id), embedder=first)

    with pytest.raises(IssueAlreadyClosedError):
        close_issue_action(repo, str(issue.id), embedder=FakeEmbedder())

    assert len(first.texts) == 1
    assert str(issue.id) in repo.embeddings


def test_build_solution_text_includes_only_available_parts(repo, issue):
    minimal = Issue(title="Bare title", component_id=issue.component_id)
    assert build_solution_text(minimal) == "Issue: Bare title"

    full = Issue(
        title="Full",
        description="Details",
        component_id=issue.component_id,
        resolution="fixed",
        resolved_by_commit_sha="deadbeef",
    )
    text = build_solution_text(full)
    assert text == "Issue: Full\n\nResolution: fixed\n\nDescription: Details\n\nCommit: deadbeef"


def test_resolve_embedding_port_returns_none_when_unavailable(monkeypatch):
    class _Unavailable:
        def is_available(self) -> bool:
            return False

    from socialseed_tasker.infrastructure import embedding_service

    monkeypatch.setattr(embedding_service, "get_embedding_service", lambda: _Unavailable())

    assert resolve_embedding_port() is None
