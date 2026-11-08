"""Run-scoped usage reporting and limit enforcement (issue #617)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.application.agent_authorization import AgentActionAuthorizer
from socialseed_tasker.auth.tokens import issue_agent_execution_token
from socialseed_tasker.infrastructure.web_api import agent_authorization
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import agent_runs

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class FakeRunStore:
    def __init__(self) -> None:
        self.run: dict[str, Any] = {
            "id": "run-1",
            "agent_id": "agent-1",
            "issue_id": "issue-1",
            "status": "running",
            "started_at": NOW,
            "total_tokens": 0,
            "total_tool_calls": 0,
            "total_cost_usd": 0.0,
            "duration_ms": None,
        }
        self.violations: list[dict[str, Any]] = []

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return dict(self.run) if run_id == self.run["id"] else None

    def add_run_usage(
        self,
        run_id: str,
        *,
        tokens: int = 0,
        cost_usd: float = 0.0,
        tool_calls: int = 0,
    ) -> dict[str, Any]:
        if run_id != self.run["id"]:
            raise LookupError(run_id)
        self.run["total_tokens"] = int(self.run.get("total_tokens") or 0) + tokens
        self.run["total_cost_usd"] = float(self.run.get("total_cost_usd") or 0.0) + cost_usd
        self.run["total_tool_calls"] = int(self.run.get("total_tool_calls") or 0) + tool_calls
        return dict(self.run)

    def stop_run_for_limit(
        self, run_id: str, *, violation: dict[str, Any]
    ) -> dict[str, Any]:
        if run_id != self.run["id"]:
            raise LookupError(run_id)
        self.run["status"] = "failed"
        self.violations.append(violation)
        return dict(self.run)


class FakeProfileStore:
    def __init__(self, limits: dict[str, Any] | None = None) -> None:
        self.profile = {
            "id": "agent-1",
            "enabled": True,
            "tools": ["neo4j_query"],
            "read_access": ["graph"],
            "propose_access": [],
            "apply_access": [],
            "limits": limits,
        }

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return self.profile if user_id == "agent-1" else None


class FakePolicyStore:
    def list_policies(self, **filters: Any) -> list[dict[str, Any]]:
        return []

    def list_for_context(
        self, *, organization_id: str | None = None, project_id: str | None = None
    ) -> list[dict[str, Any]]:
        return []


@pytest.fixture()
def env(monkeypatch: pytest.MonkeyPatch):
    for name in ("TASKER_API_KEY", "TASKER_AUTH_ENABLED", "TASKER_DATABASE_URL"):
        monkeypatch.delenv(name, raising=False)

    store = FakeRunStore()
    profiles = FakeProfileStore()

    def authorizer() -> AgentActionAuthorizer:
        return AgentActionAuthorizer(profiles, FakePolicyStore(), ["neo4j_query"])

    monkeypatch.setattr(agent_runs, "_pg_store", lambda: store)
    monkeypatch.setattr(agent_authorization, "create_agent_action_authorizer", authorizer)

    with TestClient(create_app()) as client:
        yield client, store, profiles


def _token(run_id: str = "run-1") -> str:
    return issue_agent_execution_token(
        agent_id="agent-1",
        run_id=run_id,
        issue_id="issue-1",
        project_id="project-1",
    )


def _report(client: TestClient, *, tokens: int, cost_usd: float = 0.0, token: str | None = None):
    return client.post(
        "/api/v1/runs/run-1/usage",
        json={"tokens": tokens, "cost_usd": cost_usd},
        headers={"X-Agent-Execution-Token": token or _token()},
    )


def test_usage_report_adds_server_counters(env):
    client, store, _ = env

    response = _report(client, tokens=150, cost_usd=0.25)

    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["total_tokens"] == 150
    assert data["total_cost_usd"] == 0.25
    assert store.run["status"] == "running"


def test_usage_report_stops_run_and_reports_reached_limit(env):
    client, store, profiles = env
    profiles.profile["limits"] = {"max_tokens_per_run": 100}

    response = _report(client, tokens=120)

    assert response.status_code == 409, response.text
    error = response.json()["error"]
    assert error["code"] == "AGENT_LIMIT_EXCEEDED"
    assert error["details"]["limit"] == "max_tokens_per_run"
    assert error["details"]["observed"] == 120
    assert store.run["status"] == "failed"
    assert store.violations == [error["details"]]

    # No further action can start because the run is closed.
    second = _report(client, tokens=1)
    assert second.status_code == 403


def test_usage_report_rejects_a_token_for_another_run(env):
    client, _, _ = env

    response = _report(client, tokens=1, token=_token(run_id="run-other"))

    assert response.status_code == 403


def test_usage_report_requires_an_execution_credential(env):
    client, _, _ = env

    response = client.post(
        "/api/v1/runs/run-1/usage",
        json={"tokens": 1, "cost_usd": 0.0},
    )

    assert response.status_code == 401


def test_usage_report_rejects_negative_consumption(env):
    client, _, _ = env

    response = _report(client, tokens=-1)

    assert response.status_code == 422
