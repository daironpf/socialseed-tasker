"""MCP enforcement tests for run-scoped agent authorization (issue #615)."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.auth.tokens import (
    issue_agent_execution_token,
    verify_agent_execution_token,
)
from socialseed_tasker.domain.entities import Component, Issue
from socialseed_tasker.infrastructure.web_api import agent_authorization
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import issues as issues_routes

_UNIT_DIR = Path(__file__).resolve().parents[1] / "unit"


class FakeProfileStore:
    def __init__(self) -> None:
        self.profile: dict[str, Any] = {
            "id": "agent-1",
            "enabled": True,
            "tools": ["neo4j_query"],
            "read_access": ["graph", "issues"],
            "propose_access": [],
            "apply_access": [],
        }
        self.issue_id = ""
        self.runs: list[dict[str, Any]] = []

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return self.profile if user_id == self.profile["id"] else None

    def create_run(self, agent_id: str, *, issue_id: str, model: str | None = None):
        run = {
            "id": "run-1",
            "agent_id": agent_id,
            "issue_id": issue_id,
            "model": model,
            "status": "running",
        }
        self.runs.append(run)
        self.issue_id = issue_id
        return run

    def update_run(self, run_id: str, **fields: Any):
        self.runs[0].update(fields)
        return self.runs[0]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        if run_id != "run-1":
            return None
        return {
            "id": run_id,
            "agent_id": "agent-1",
            "issue_id": self.issue_id,
            "status": "running",
        }


class FakePolicyStore:
    def __init__(self) -> None:
        self.policies: list[dict[str, Any]] = []

    def list_policies(self, **filters: Any) -> list[dict[str, Any]]:
        return [
            policy
            for policy in self.policies
            if all(policy.get(key) == value for key, value in filters.items())
        ]

    def list_for_context(
        self, *, organization_id: str | None = None, project_id: str | None = None
    ) -> list[dict[str, Any]]:
        return [
            policy
            for policy in self.policies
            if policy.get("is_active", True)
            and (
                policy.get("scope_type") == "project"
                and policy.get("scope_id") == project_id
                or policy.get("scope_type") == "organization"
                and policy.get("scope_id") == organization_id
            )
        ]


@pytest.fixture()
def client_and_context(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("TASKER_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("TASKER_API_KEY", raising=False)
    if str(_UNIT_DIR) not in sys.path:
        sys.path.insert(0, str(_UNIT_DIR))
    from test_api import MockRepository

    repository = MockRepository()
    project_id = str(uuid4())
    component = repository.create_component(
        Component(name="backend", project="demo", project_id=project_id)
    )
    issue = repository.create_issue(
        Issue(title="Authorized issue", component_id=component.id)
    )
    other_component = repository.create_component(
        Component(name="other", project="other", project_id=str(uuid4()))
    )
    other_issue = repository.create_issue(
        Issue(title="Out of scope issue", component_id=other_component.id)
    )
    repository.seed = {
        "issue": str(issue.id),
        "other_issue": str(other_issue.id),
    }

    profiles = FakeProfileStore()
    policies = FakePolicyStore()
    profiles.issue_id = str(issue.id)
    monkeypatch.setattr(agent_authorization, "create_agent_profile_store", lambda: profiles)

    def create_authorizer():
        from socialseed_tasker.application.agent_authorization import AgentActionAuthorizer

        return AgentActionAuthorizer(profiles, policies, ["neo4j_query"])

    monkeypatch.setattr(agent_authorization, "create_agent_action_authorizer", create_authorizer)
    with TestClient(create_app(repository=repository)) as client:
        yield client, repository.seed, project_id, profiles, policies


def _token(project_id: str, issue_id: str) -> str:
    return issue_agent_execution_token(
        agent_id="agent-1",
        run_id="run-1",
        issue_id=issue_id,
        project_id=project_id,
    )


def _initialize(client: TestClient, headers: dict[str, str] | None = None) -> None:
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "agent-auth-test", "version": "1"},
            },
        },
        headers=headers or {},
    )
    assert response.status_code == 200
    initialized = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "method": "notifications/initialized"},
        headers=headers or {},
    )
    assert initialized.status_code == 202


def _call_issue(
    client: TestClient,
    issue_id: str,
    token: str,
) -> dict[str, Any]:
    response = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "issue_detail",
                "arguments": {"issue_id": issue_id},
            },
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    return response.json()["result"]


def test_agent_token_authorizes_only_resources_in_its_project(client_and_context):
    client, seed, project_id, _, _ = client_and_context
    _initialize(client)
    token = _token(project_id, seed["issue"])

    allowed = _call_issue(client, seed["issue"], token)
    denied = _call_issue(client, seed["other_issue"], token)

    assert allowed["isError"] is not True
    assert "Authorized issue" in allowed["content"][0]["text"]
    assert denied["isError"] is True


def test_policy_changes_and_run_closure_apply_to_subsequent_tool_calls(
    client_and_context,
):
    client, seed, project_id, profiles, policies = client_and_context
    _initialize(client)
    token = _token(project_id, seed["issue"])

    assert _call_issue(client, seed["issue"], token)["isError"] is not True
    profiles.profile["enabled"] = False
    assert _call_issue(client, seed["issue"], token)["isError"] is True
    profiles.profile["enabled"] = True
    policies.policies.append(
        {
            "id": "deny-issues",
            "scope_type": "project",
            "scope_id": project_id,
            "is_active": True,
            "read_access": ["graph"],
        }
    )
    denied_by_policy = _call_issue(client, seed["issue"], token)
    assert denied_by_policy["isError"] is True

    policies.policies.clear()
    profiles.get_run = lambda run_id: {
        "id": run_id,
        "agent_id": "agent-1",
        "issue_id": seed["issue"],
        "status": "completed",
    }
    denied_after_close = _call_issue(client, seed["issue"], token)
    assert denied_after_close["isError"] is True


def test_execution_token_is_accepted_only_by_mcp_when_api_auth_is_enabled(
    monkeypatch: pytest.MonkeyPatch,
    client_and_context,
):
    client, seed, project_id, _, _ = client_and_context
    monkeypatch.setenv("TASKER_AUTH_ENABLED", "true")
    monkeypatch.setenv("TASKER_API_KEY", "mcp-test-key")
    # Rebuild the app so the middleware captures the auth settings.
    repository = client.app.state.repository
    with TestClient(create_app(repository=repository)) as secure_client:
        _initialize(secure_client, {"Authorization": "Bearer mcp-test-key"})
        token = _token(project_id, seed["issue"])
        result = _call_issue(secure_client, seed["issue"], token)
        assert result["isError"] is not True
        response = secure_client.get(
            "/api/v1/agents/profiles",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


def test_agent_start_returns_scoped_token_and_denial_has_no_run_side_effect(
    monkeypatch: pytest.MonkeyPatch,
    client_and_context,
):
    client, seed, project_id, profiles, _ = client_and_context
    decisions = [SimpleNamespace(allowed=True), SimpleNamespace(allowed=False)]

    class AuthorizerStub:
        def authorize(self, **kwargs: Any):
            return decisions.pop(0)

    monkeypatch.setattr(
        issues_routes,
        "create_agent_action_authorizer",
        lambda: AuthorizerStub(),
    )
    monkeypatch.setattr(
        issues_routes,
        "create_agent_profile_store",
        lambda: profiles,
    )

    started = client.post(
        f"/api/v1/issues/{seed['issue']}/agent/start",
        json={"agent_id": "agent-1"},
    )

    assert started.status_code == 200
    claims = verify_agent_execution_token(
        started.headers["X-Agent-Execution-Token"]
    )
    assert claims is not None
    assert claims["sub"] == "agent-1"
    assert claims["issue_id"] == seed["issue"]
    assert claims["project_id"] == project_id
    assert len(profiles.runs) == 1
    openapi_response = client.get("/openapi.json").json()["paths"][
        "/api/v1/issues/{issue_id}/agent/start"
    ]["post"]["responses"]["200"]
    assert "X-Agent-Execution-Token" in openapi_response["headers"]

    denied = client.post(
        f"/api/v1/issues/{seed['other_issue']}/agent/start",
        json={"agent_id": "agent-1"},
    )
    assert denied.status_code == 403
    assert len(profiles.runs) == 1
