"""Tests for the agent lifecycle aliases and issue-update SSE stream (issue #530)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
from fastapi import Request
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers.realtime import (
    RealtimeHub,
    issue_updates_stream,
)

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
            "title": "Agent lifecycle issue",
            "component_id": component_id,
            "description": "Issue used by the agent lifecycle tests",
            "priority": "HIGH",
        },
    )
    return resp.json()["data"]["id"]


class TestStartStopAgentAliases:
    def test_start_agent_toggles_flag_on(self, client, issue_id):
        resp = client.post(f"/api/v1/issues/{issue_id}/start-agent", json={})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["agent_working"] is True
        assert data["agent_working_started_at"] is not None

    def test_start_agent_conflict_when_already_working(self, client, issue_id):
        client.post(f"/api/v1/issues/{issue_id}/start-agent", json={})
        resp = client.post(f"/api/v1/issues/{issue_id}/start-agent", json={})
        assert resp.status_code == 409

    def test_start_agent_not_found(self, client):
        resp = client.post("/api/v1/issues/nonexistent-id/start-agent", json={})
        assert resp.status_code == 404

    def test_stop_agent_toggles_flag_off(self, client, issue_id):
        client.post(f"/api/v1/issues/{issue_id}/start-agent", json={})
        resp = client.post(f"/api/v1/issues/{issue_id}/stop-agent", json={})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["agent_working"] is False

    def test_stop_agent_conflict_when_idle(self, client, issue_id):
        resp = client.post(f"/api/v1/issues/{issue_id}/stop-agent", json={})
        assert resp.status_code == 409

    def test_stop_agent_not_found(self, client):
        resp = client.post("/api/v1/issues/nonexistent-id/stop-agent", json={})
        assert resp.status_code == 404

    def test_aliases_accept_explicit_agent_id(self, client, issue_id):
        start = client.post(
            f"/api/v1/issues/{issue_id}/start-agent",
            json={"agent_id": "agent-001"},
        )
        assert start.status_code == 200
        stop = client.post(
            f"/api/v1/issues/{issue_id}/stop-agent",
            json={"agent_id": "agent-001"},
        )
        assert stop.status_code == 200


class TestIssueUpdatesStream:
    def test_stream_route_registered_before_dynamic_issue_route(self, app):
        paths = [getattr(route, "path", None) for route in app.routes]
        assert "/api/v1/issues/stream" in paths
        assert (
            paths.index("/api/v1/issues/stream")
            < paths.index("/api/v1/issues/{issue_id}")
        )

    def test_stream_emits_connected_frame(self, app):
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/v1/issues/stream",
            "raw_path": b"/api/v1/issues/stream",
            "query_string": b"",
            "root_path": "",
            "headers": [],
            "client": ("testclient", 50000),
            "server": ("testserver", 80),
            "app": app,
            "router": app.router,
        }

        async def receive():
            return {"type": "http.disconnect"}

        async def read_first_frame() -> str:
            response = issue_updates_stream(Request(scope, receive))
            iterator = response.body_iterator
            try:
                return await iterator.__anext__()
            finally:
                await iterator.aclose()

        frame = asyncio.run(read_first_frame())
        assert frame.startswith("event: connected\n")
        assert "data: " in frame

    def test_start_agent_broadcasts_issue_updated(self, client, app, issue_id):
        hub = RealtimeHub()
        app.state.realtime_hub = hub
        queue = hub.subscribe_issues()

        resp = client.post(f"/api/v1/issues/{issue_id}/start-agent", json={})
        assert resp.status_code == 200

        entry = queue.get_nowait()
        assert entry["event"] == "issue-updated"
        assert entry["data"]["issue_id"] == issue_id
        assert entry["data"]["agent_working"] is True
        assert entry["data"]["agent_working_started_at"] is not None

    def test_stop_agent_broadcasts_flag_cleared(self, client, app, issue_id):
        hub = RealtimeHub()
        app.state.realtime_hub = hub
        queue = hub.subscribe_issues()
        client.post(f"/api/v1/issues/{issue_id}/start-agent", json={})
        queue.get_nowait()

        resp = client.post(f"/api/v1/issues/{issue_id}/stop-agent", json={})
        assert resp.status_code == 200

        entry = queue.get_nowait()
        assert entry["event"] == "issue-updated"
        assert entry["data"]["agent_working"] is False

    def test_patch_agent_working_broadcasts(self, client, app, issue_id):
        hub = RealtimeHub()
        app.state.realtime_hub = hub
        queue = hub.subscribe_issues()

        resp = client.patch(f"/api/v1/issues/{issue_id}", json={"agent_working": True})
        assert resp.status_code == 200

        entry = queue.get_nowait()
        assert entry["event"] == "issue-updated"
        assert entry["data"]["issue_id"] == issue_id
        assert entry["data"]["agent_working"] is True

    def test_patch_without_agent_flag_does_not_broadcast(self, client, app, issue_id):
        hub = RealtimeHub()
        app.state.realtime_hub = hub
        queue = hub.subscribe_issues()

        resp = client.patch(f"/api/v1/issues/{issue_id}", json={"title": "Renamed"})
        assert resp.status_code == 200
        assert queue.empty()
