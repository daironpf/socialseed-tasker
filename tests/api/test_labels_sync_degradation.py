"""POST /labels/sync degradation (issue #589).

Without ``GITHUB_TOKEN`` the endpoint used to raise httpx
``Illegal header value b'token '`` (500): the adapter built
``Authorization: token <vacío>`` unconditionally and the handler's
``except Exception`` re-wrapped it as 500. Fixed with: repo guard (503),
token guard (503 ``GITHUB_TOKEN_NOT_CONFIGURED``), defensive headers
(set ``Authorization`` only when a stripped token exists) and
``except HTTPException: raise`` so guards never get re-wrapped.
"""

from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app

FAKE_TOKEN = "ghp_faketoken_for_tests_0123456789abcdef"


class _RepoWithSync:
    def __init__(self) -> None:
        self.last_adapter: Any = None

    def sync_labels_from_github(self, adapter: Any) -> int:
        self.last_adapter = adapter
        return 7

    def get_all_labels(self) -> list[dict[str, Any]]:
        return []


class _RepoWithoutSync:
    """Repository lacking sync_labels_from_github (e.g. None-like mode)."""


def _make_client(repo: Any) -> TestClient:
    return TestClient(create_app(repository=repo, neo4j_driver=None))


def _no_secret_tokens(monkeypatch: pytest.MonkeyPatch) -> None:
    class _EmptySecrets:
        def get_github_token(self, repo: str = "") -> None:
            return None

    monkeypatch.setattr(
        "socialseed_tasker.application.secret_manager.get_secret_manager",
        lambda: _EmptySecrets(),
        raising=True,
    )
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)


def test_labels_sync_without_token_returns_503_not_500(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _no_secret_tokens(monkeypatch)
    client = _make_client(_RepoWithSync())

    resp = client.post("/api/v1/labels/sync")
    assert resp.status_code == 503, resp.text
    assert "GITHUB_TOKEN_NOT_CONFIGURED" in resp.json()["detail"]
    assert "Illegal header" not in resp.text


def test_labels_sync_without_repository_returns_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _no_secret_tokens(monkeypatch)
    client = _make_client(_RepoWithoutSync())

    resp = client.post("/api/v1/labels/sync")
    assert resp.status_code == 503, resp.text
    assert resp.json()["detail"] == "Neo4j not available"


def test_labels_sync_happy_path_with_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _no_secret_tokens(monkeypatch)
    monkeypatch.setenv("GITHUB_TOKEN", FAKE_TOKEN)
    repo = _RepoWithSync()
    client = _make_client(repo)

    resp = client.post("/api/v1/labels/sync")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == {"synced": 7}
    assert repo.last_adapter is not None
    assert repo.last_adapter.has_token is True
    auth = repo.last_adapter._client.headers.get("Authorization")
    assert auth == f"token {FAKE_TOKEN}"


def test_github_adapter_without_token_omits_authorization_header(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _no_secret_tokens(monkeypatch)
    from socialseed_tasker.infrastructure.github_adapter import GitHubAdapter

    adapter = GitHubAdapter()
    try:
        assert adapter.has_token is False
        assert adapter.is_configured is False
        assert "Authorization" not in adapter._client.headers
    finally:
        adapter.close()


def test_github_adapter_whitespace_token_counts_as_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _no_secret_tokens(monkeypatch)
    monkeypatch.setenv("GITHUB_TOKEN", "   ")
    from socialseed_tasker.infrastructure.github_adapter import GitHubAdapter

    adapter = GitHubAdapter()
    try:
        assert adapter.has_token is False
        assert "Authorization" not in adapter._client.headers
    finally:
        adapter.close()
