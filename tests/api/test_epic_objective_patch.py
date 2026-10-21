"""PATCH /epics and /objectives contracts (issue #579).

Empty body used to reach the mixin, which built ``SET  RETURN e`` (no
expressions) and returned 500 ``CypherSyntaxError``. Now the router rejects the
empty update with 422 and the mixin only interpolates allowlisted keys.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app


class _SpyRepository:
    """Records update calls; anything else is never expected in these tests."""

    def __init__(self) -> None:
        self.epic_updates: list[tuple[str, dict]] = []
        self.objective_updates: list[tuple[str, dict]] = []

    def update_epic(self, epic_id: str, updates: dict) -> None:
        self.epic_updates.append((epic_id, updates))

    def update_objective(self, objective_id: str, updates: dict) -> None:
        self.objective_updates.append((objective_id, updates))


@pytest.fixture()
def repo() -> _SpyRepository:
    return _SpyRepository()


@pytest.fixture()
def client(repo: _SpyRepository):
    return TestClient(create_app(repository=repo))


def test_patch_epic_empty_body_returns_422_not_500(client: TestClient, repo: _SpyRepository) -> None:
    resp = client.patch("/api/v1/epics/any-id", json={})

    assert resp.status_code == 422
    assert "empty update" in resp.json()["detail"]
    assert repo.epic_updates == []


def test_patch_objective_empty_body_returns_422_not_500(client: TestClient, repo: _SpyRepository) -> None:
    resp = client.patch("/api/v1/objectives/any-id", json={})

    assert resp.status_code == 422
    assert "empty update" in resp.json()["detail"]
    assert repo.objective_updates == []


def test_patch_epic_with_fields_updates_and_returns_200(client: TestClient, repo: _SpyRepository) -> None:
    resp = client.patch("/api/v1/epics/epic-9", json={"name": "Renamed", "status": "IN_PROGRESS"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["updated"] == "epic-9"
    assert repo.epic_updates == [("epic-9", {"name": "Renamed", "status": "IN_PROGRESS"})]


def test_patch_objective_with_fields_updates_and_returns_200(client: TestClient, repo: _SpyRepository) -> None:
    resp = client.patch("/api/v1/objectives/obj-9", json={"quarter": "2026Q4"})

    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["updated"] == "obj-9"
    assert repo.objective_updates == [("obj-9", {"quarter": "2026Q4"})]


def test_patch_epic_without_body_returns_422(client: TestClient, repo: _SpyRepository) -> None:
    resp = client.patch("/api/v1/epics/any-id")

    assert resp.status_code == 422
    assert repo.epic_updates == []
