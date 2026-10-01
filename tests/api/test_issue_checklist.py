"""Tests for the interactive task checklist field (issue #531)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers.realtime import RealtimeHub

_UNIT_DIR = Path(__file__).resolve().parents[1] / "unit"


@pytest.fixture()
def repo():
    # Reuse the in-memory repository from tests/unit/test_api.py; the path
    # insert keeps this file runnable in isolation (tests/ is not a package).
    if str(_UNIT_DIR) not in sys.path:
        sys.path.insert(0, str(_UNIT_DIR))
    from test_api import MockRepository

    return MockRepository()


@pytest.fixture()
def app(repo):
    return create_app(repository=repo)


@pytest.fixture()
def client(app):
    return TestClient(app)


@pytest.fixture()
def issue_id(client):
    component = client.post(
        "/api/v1/components",
        json={"name": "Backend", "project": "test-project"},
    )
    component_id = component.json()["data"]["id"]
    resp = client.post(
        "/api/v1/issues",
        json={
            "title": "Checklist issue",
            "component_id": component_id,
            "description": "Issue used by the task checklist tests",
        },
    )
    return resp.json()["data"]["id"]


class TestTaskChecklist:
    def test_created_issue_returns_empty_checklist(self, client, issue_id):
        resp = client.get(f"/api/v1/issues/{issue_id}")
        assert resp.status_code == 200
        assert resp.json()["data"]["task_checklist"] == {}

    def test_patch_task_checklist_persists(self, client, issue_id):
        resp = client.patch(
            f"/api/v1/issues/{issue_id}",
            json={"task_checklist": {"install dependencies": True, "run tests": False}},
        )
        assert resp.status_code == 200
        expected = {"install dependencies": True, "run tests": False}
        assert resp.json()["data"]["task_checklist"] == expected

        again = client.get(f"/api/v1/issues/{issue_id}")
        assert again.json()["data"]["task_checklist"] == expected

    def test_patch_task_checklist_replaces_previous_state(self, client, issue_id):
        client.patch(
            f"/api/v1/issues/{issue_id}",
            json={"task_checklist": {"item one": True, "item two": False}},
        )
        resp = client.patch(
            f"/api/v1/issues/{issue_id}",
            json={"task_checklist": {"item two": True}},
        )
        assert resp.json()["data"]["task_checklist"] == {"item two": True}

    def test_patch_task_checklist_broadcasts_issue_updated(self, client, app, issue_id):
        hub = RealtimeHub()
        app.state.realtime_hub = hub
        queue = hub.subscribe_issues()

        resp = client.patch(
            f"/api/v1/issues/{issue_id}",
            json={"task_checklist": {"deploy to staging": True}},
        )
        assert resp.status_code == 200

        entry = queue.get_nowait()
        assert entry["event"] == "issue-updated"
        assert entry["data"]["issue_id"] == issue_id
        assert entry["data"]["task_checklist"] == {"deploy to staging": True}

    def test_patch_agent_flag_and_checklist_broadcast_once(self, client, app, issue_id):
        hub = RealtimeHub()
        app.state.realtime_hub = hub
        queue = hub.subscribe_issues()

        resp = client.patch(
            f"/api/v1/issues/{issue_id}",
            json={"agent_working": True, "task_checklist": {"step": True}},
        )
        assert resp.status_code == 200

        entry = queue.get_nowait()
        assert entry["event"] == "issue-updated"
        assert entry["data"]["agent_working"] is True
        assert entry["data"]["task_checklist"] == {"step": True}
        assert queue.empty()

    def test_patch_without_checklist_or_agent_flag_does_not_broadcast(self, client, app, issue_id):
        hub = RealtimeHub()
        app.state.realtime_hub = hub
        queue = hub.subscribe_issues()

        resp = client.patch(f"/api/v1/issues/{issue_id}", json={"priority": "HIGH"})
        assert resp.status_code == 200
        assert queue.empty()

    def test_patch_invalid_task_checklist_value_rejected(self, client, issue_id):
        resp = client.patch(
            f"/api/v1/issues/{issue_id}",
            json={"task_checklist": {"item": "banana"}},
        )
        assert resp.status_code == 422
