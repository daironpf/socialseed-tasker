"""API authorization and lifecycle tests for agent approvals (issue #616)."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.application.agent_authorization import AgentActionAuthorizer
from socialseed_tasker.auth.rbac import RBAC
from socialseed_tasker.auth.tokens import issue_agent_execution_token, issue_tokens
from socialseed_tasker.domain.entities import Component, Issue
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import agent_approvals as approval_routes
from tests.fakes.fake_agent_approvals import FakeAgentApprovalStore

_UNIT_DIR = Path(__file__).resolve().parents[1] / "unit"

ADMIN_JWT = issue_tokens({"id": "human-admin", "username": "human-admin", "role": "ADMIN", "permissions": ["admin"]})[
    "access_token"
]
DEV_JWT = issue_tokens(
    {"id": "human-dev", "username": "human-dev", "role": "DEVELOPER", "permissions": ["read:context"]}
)["access_token"]

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class FakeAgentProfileStore:
    def __init__(self) -> None:
        self.profile: dict[str, Any] = {
            "id": "agent-1",
            "enabled": True,
            "tools": ["neo4j_query"],
            "read_access": ["graph", "issues"],
            "propose_access": ["graph"],
            "apply_access": ["graph"],
        }
        self.run: dict[str, Any] = {
            "id": "run-1",
            "agent_id": "agent-1",
            "issue_id": "",
            "status": "running",
        }

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return self.profile if user_id == self.profile["id"] else None

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        return dict(self.run) if run_id == self.run["id"] else None


class FakePolicyStore:
    def list_policies(self, **filters: Any) -> list[dict[str, Any]]:
        return []

    def list_for_context(
        self, *, organization_id: str | None = None, project_id: str | None = None
    ) -> list[dict[str, Any]]:
        return []


class Clock:
    def __init__(self, value: datetime = NOW) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _body(**overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "action": "apply",
        "tool": "neo4j_query",
        "resource_scope": "graph",
        "target": "production",
        "expected_effect": "archive the selected nodes",
        "action_payload": {"cypher": "MATCH (n) RETURN n"},
        "expires_in_seconds": 600,
        "metadata": {
            "title": "Archive production nodes",
            "type": "schema_migration",
            "severity": "HIGH",
        },
    }
    body.update(overrides)
    return body


@pytest.fixture()
def env(monkeypatch: pytest.MonkeyPatch):
    for name in (
        "TASKER_AUTH_USERS",
        "TASKER_AUTH_ENABLED",
        "TASKER_API_KEY",
        "TASKER_REDIS_URL",
        "TASKER_DATABASE_URL",
    ):
        monkeypatch.delenv(name, raising=False)

    if str(_UNIT_DIR) not in sys.path:
        sys.path.insert(0, str(_UNIT_DIR))
    from test_api import MockRepository

    repository = MockRepository()
    project_id = str(uuid4())
    component = repository.create_component(Component(name="backend", project="demo", project_id=project_id))
    issue = repository.create_issue(Issue(title="Approve graph change", component_id=component.id))
    other_component = repository.create_component(Component(name="other", project="other", project_id=str(uuid4())))
    other_issue = repository.create_issue(Issue(title="Out of scope", component_id=other_component.id))

    profiles = FakeAgentProfileStore()
    profiles.run["issue_id"] = str(issue.id)
    store = FakeAgentApprovalStore()
    clock = Clock()

    def create_profiles() -> FakeAgentProfileStore:
        return profiles

    def create_authorizer() -> AgentActionAuthorizer:
        return AgentActionAuthorizer(profiles, FakePolicyStore(), ["neo4j_query"])

    def create_service():
        from socialseed_tasker.application.agent_approvals import AgentApprovalService

        return AgentApprovalService(store, clock=clock)

    monkeypatch.setattr(approval_routes, "create_agent_profile_store", create_profiles)
    monkeypatch.setattr(approval_routes, "create_agent_action_authorizer", create_authorizer)
    monkeypatch.setattr(approval_routes, "create_agent_approval_service", create_service)

    app = create_app(repository=repository)
    app.state.container = SimpleNamespace(rbac=RBAC())
    with TestClient(app) as client:
        yield SimpleNamespace(
            client=client,
            project_id=project_id,
            issue_id=str(issue.id),
            other_issue_id=str(other_issue.id),
            profiles=profiles,
            store=store,
            clock=clock,
        )


def _agent_token(env: SimpleNamespace, *, issue_id: str | None = None) -> str:
    return issue_agent_execution_token(
        agent_id="agent-1",
        run_id="run-1",
        issue_id=issue_id or env.issue_id,
        project_id=env.project_id,
    )


def _create(env: SimpleNamespace, **overrides: Any) -> dict[str, Any]:
    response = env.client.post(
        "/api/v1/agent-approvals",
        json=_body(**overrides),
        headers=_headers(_agent_token(env)),
    )
    return response


def _approved(env: SimpleNamespace) -> dict[str, Any]:
    created = _create(env)
    assert created.status_code == 200, created.text
    approval_id = created.json()["data"]["id"]
    decision = env.client.post(
        f"/api/v1/agent-approvals/{approval_id}/approve",
        json={"feedback": "approved by human"},
        headers=_headers(ADMIN_JWT),
    )
    assert decision.status_code == 200, decision.text
    return decision.json()["data"]


def test_agent_requests_approval_and_human_inbox_reads_server_state(env):
    created = _create(env)
    assert created.status_code == 200, created.text
    data = created.json()["data"]
    assert data["status"] == "pending"
    assert data["agent_id"] == "agent-1"
    assert data["run_id"] == "run-1"
    assert data["issue_id"] == env.issue_id
    assert data["request_metadata"]["title"] == "Archive production nodes"

    unauthorized = env.client.get("/api/v1/agent-approvals")
    assert unauthorized.status_code == 403

    inbox = env.client.get("/api/v1/agent-approvals", headers=_headers(ADMIN_JWT))
    assert inbox.status_code == 200, inbox.text
    assert [row["id"] for row in inbox.json()["data"]] == [data["id"]]


def test_approval_requires_an_agent_execution_credential(env):
    response = env.client.post(
        "/api/v1/agent-approvals",
        json=_body(),
        headers=_headers(ADMIN_JWT),
    )
    assert response.status_code == 401


def test_agent_cannot_decide_its_own_approval(env):
    created = _create(env)
    assert created.status_code == 200, created.text
    approval_id = created.json()["data"]["id"]

    response = env.client.post(
        f"/api/v1/agent-approvals/{approval_id}/approve",
        json={},
        headers=_headers(_agent_token(env)),
    )

    assert response.status_code == 403
    assert env.store.get_approval(approval_id)["status"] == "pending"


def test_developer_cannot_decide_approvals(env):
    created = _create(env)
    approval_id = created.json()["data"]["id"]

    response = env.client.post(
        f"/api/v1/agent-approvals/{approval_id}/approve",
        json={},
        headers=_headers(DEV_JWT),
    )

    assert response.status_code == 403
    assert env.store.get_approval(approval_id)["status"] == "pending"


def test_approved_action_executes_once_and_rejects_reuse(env):
    approved = _approved(env)

    executed = env.client.post(
        f"/api/v1/agent-approvals/{approved['id']}/execute",
        json=_body(),
        headers=_headers(_agent_token(env)),
    )
    assert executed.status_code == 200, executed.text
    assert executed.json()["data"]["executed_at"].startswith("2026-01-01T12:00:00")

    reused = env.client.post(
        f"/api/v1/agent-approvals/{approved['id']}/execute",
        json=_body(),
        headers=_headers(_agent_token(env)),
    )
    assert reused.status_code == 409
    assert reused.json()["error"]["code"] == "APPROVAL_ALREADY_USED"


def test_changed_payload_after_approval_is_rejected(env):
    approved = _approved(env)

    changed = env.client.post(
        f"/api/v1/agent-approvals/{approved['id']}/execute",
        json=_body(action_payload={"cypher": "MATCH (n) DELETE n"}),
        headers=_headers(_agent_token(env)),
    )

    assert changed.status_code == 409
    assert changed.json()["error"]["code"] == "APPROVAL_ACTION_CHANGED"
    assert env.store.get_approval(approved["id"])["executed_at"] is None


def test_rejection_and_revocation_are_visible_and_block_execution(env):
    rejected = _create(env)
    rejected_id = rejected.json()["data"]["id"]
    response = env.client.post(
        f"/api/v1/agent-approvals/{rejected_id}/reject",
        json={"feedback": "too risky"},
        headers=_headers(ADMIN_JWT),
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "rejected"

    rejected_execution = env.client.post(
        f"/api/v1/agent-approvals/{rejected_id}/execute",
        json=_body(),
        headers=_headers(_agent_token(env)),
    )
    assert rejected_execution.status_code == 409
    assert rejected_execution.json()["error"]["code"] == "APPROVAL_REJECTED"

    approved = _approved(env)
    revoked = env.client.post(
        f"/api/v1/agent-approvals/{approved['id']}/revoke",
        json={"feedback": "scope changed"},
        headers=_headers(ADMIN_JWT),
    )
    assert revoked.status_code == 200
    assert revoked.json()["data"]["status"] == "revoked"

    revoked_execution = env.client.post(
        f"/api/v1/agent-approvals/{approved['id']}/execute",
        json=_body(),
        headers=_headers(_agent_token(env)),
    )
    assert revoked_execution.status_code == 409
    assert revoked_execution.json()["error"]["code"] == "APPROVAL_REVOKED"


def test_expired_approval_blocks_execution(env):
    created = _create(env, expires_in_seconds=1)
    approval_id = created.json()["data"]["id"]
    decision = env.client.post(
        f"/api/v1/agent-approvals/{approval_id}/approve",
        json={},
        headers=_headers(ADMIN_JWT),
    )
    assert decision.status_code == 200

    env.clock.value = env.clock.value.replace(year=2027)

    executed = env.client.post(
        f"/api/v1/agent-approvals/{approval_id}/execute",
        json=_body(),
        headers=_headers(_agent_token(env)),
    )
    assert executed.status_code == 409
    assert executed.json()["error"]["code"] == "APPROVAL_EXPIRED"


def test_inactive_run_cannot_request_or_execute(env):
    env.profiles.run["status"] = "completed"

    created = _create(env)
    assert created.status_code == 403

    env.profiles.run["status"] = "running"
    approved = _approved(env)
    env.profiles.run["status"] = "completed"

    executed = env.client.post(
        f"/api/v1/agent-approvals/{approved['id']}/execute",
        json=_body(),
        headers=_headers(_agent_token(env)),
    )
    assert executed.status_code == 403


def test_execution_token_for_another_issue_is_rejected(env):
    response = _create(env, action="apply")
    assert response.status_code == 200

    other = env.client.post(
        "/api/v1/agent-approvals",
        json=_body(),
        headers=_headers(_agent_token(env, issue_id=env.other_issue_id)),
    )
    assert other.status_code == 403


def test_unauthorized_action_cannot_request_approval(env):
    env.profiles.profile["apply_access"] = ["issues"]

    response = _create(env)

    assert response.status_code == 403
    assert env.store.rows == {}
