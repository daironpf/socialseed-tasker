"""Lifecycle tests for human approvals bound to agent actions (issue #616)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from socialseed_tasker.application.agent_approvals import (
    AgentApprovalError,
    AgentApprovalService,
)
from socialseed_tasker.domain.agent_approval import action_fingerprint
from tests.fakes.fake_agent_approvals import FakeAgentApprovalStore

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class Clock:
    def __init__(self, value: datetime = NOW) -> None:
        self.value = value

    def __call__(self) -> datetime:
        return self.value

    def advance(self, **kwargs: int) -> None:
        self.value = self.value + timedelta(**kwargs)


def _request(service: AgentApprovalService, **overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "run_id": "run-1",
        "agent_id": "agent-1",
        "issue_id": "issue-1",
        "project_id": "project-1",
        "action": "apply",
        "tool": "neo4j_query",
        "resource_scope": "graph",
        "target": "production",
        "expected_effect": "archive the selected nodes",
        "action_payload": {"cypher": "MATCH (n) RETURN n"},
        "expires_in_seconds": 600,
        "request_metadata": {"title": "Archive nodes"},
    }
    fields.update(overrides)
    return service.request_approval(**fields)


def _execute(service: AgentApprovalService, approval_id: str, **overrides: Any) -> dict[str, Any]:
    fields: dict[str, Any] = {
        "run_id": "run-1",
        "agent_id": "agent-1",
        "action": "apply",
        "tool": "neo4j_query",
        "resource_scope": "graph",
        "target": "production",
        "expected_effect": "archive the selected nodes",
        "action_payload": {"cypher": "MATCH (n) RETURN n"},
        "authorization_allowed": True,
    }
    fields.update(overrides)
    return service.execute(approval_id, **fields)


@pytest.fixture()
def context():
    store = FakeAgentApprovalStore()
    clock = Clock()
    service = AgentApprovalService(store, clock=clock)
    return service, store, clock


def test_request_is_pending_and_bound_to_the_exact_action(context):
    service, _, _ = context
    row = _request(service)

    assert row["status"] == "pending"
    assert row["executed_at"] is None
    assert row["action_fingerprint"] == action_fingerprint(
        action="apply",
        tool="neo4j_query",
        resource_scope="graph",
        target="production",
        expected_effect="archive the selected nodes",
        action_payload={"cypher": "MATCH (n) RETURN n"},
    )


def test_changing_the_payload_changes_the_fingerprint(context):
    service, _, _ = context
    first = _request(service)
    second = _request(service, action_payload={"cypher": "MATCH (n) DELETE n"})

    assert first["action_fingerprint"] != second["action_fingerprint"]


def test_approved_action_executes_exactly_once(context):
    service, _, _ = context
    row = _request(service)
    service.approve(row["id"], actor_id="human-admin")

    consumed = _execute(service, row["id"])

    assert consumed["executed_at"] == NOW
    with pytest.raises(AgentApprovalError) as exc:
        _execute(service, row["id"])
    assert exc.value.code == "approval_already_used"


def test_changed_action_cannot_reuse_an_approval(context):
    service, store, _ = context
    row = _request(service)
    service.approve(row["id"], actor_id="human-admin")

    with pytest.raises(AgentApprovalError) as exc:
        _execute(service, row["id"], action_payload={"cypher": "MATCH (n) DELETE n"})

    assert exc.value.code == "approval_action_changed"
    assert store.get_approval(row["id"])["executed_at"] is None


def test_rejection_leaves_the_action_unexecuted(context):
    service, store, _ = context
    row = _request(service)
    rejected = service.reject(row["id"], actor_id="human-admin", feedback="too risky")

    assert rejected["status"] == "rejected"
    assert rejected["feedback"] == "too risky"
    with pytest.raises(AgentApprovalError) as exc:
        _execute(service, row["id"])
    assert exc.value.code == "approval_rejected"
    assert store.get_approval(row["id"])["executed_at"] is None


def test_revocation_blocks_a_previously_approved_action(context):
    service, store, _ = context
    row = _request(service)
    service.approve(row["id"], actor_id="human-admin")
    revoked = service.revoke(row["id"], actor_id="human-admin", feedback="scope changed")

    assert revoked["status"] == "revoked"
    assert revoked["feedback"] == "scope changed"
    with pytest.raises(AgentApprovalError) as exc:
        _execute(service, row["id"])
    assert exc.value.code == "approval_revoked"
    assert store.get_approval(row["id"])["executed_at"] is None


def test_expiry_prevents_execution_and_is_visible(context):
    service, store, clock = context
    row = _request(service, expires_in_seconds=60)
    service.approve(row["id"], actor_id="human-admin")
    clock.advance(seconds=61)

    with pytest.raises(AgentApprovalError) as exc:
        _execute(service, row["id"])

    assert exc.value.code == "approval_expired"
    assert service.get_approval(row["id"])["status"] == "expired"
    assert store.get_approval(row["id"])["executed_at"] is None


def test_expired_request_cannot_be_approved(context):
    service, _, clock = context
    row = _request(service, expires_in_seconds=60)
    clock.advance(seconds=61)

    with pytest.raises(AgentApprovalError) as exc:
        service.approve(row["id"], actor_id="human-admin")

    assert exc.value.code == "approval_expired"


def test_no_deadline_never_implies_approval(context):
    service, _, clock = context
    row = _request(service, expires_in_seconds=None)
    clock.advance(days=365)

    assert service.get_approval(row["id"])["status"] == "pending"
    with pytest.raises(AgentApprovalError) as exc:
        _execute(service, row["id"])
    assert exc.value.code == "approval_pending"


def test_execution_requires_the_original_agent_and_run(context):
    service, store, _ = context
    row = _request(service)
    service.approve(row["id"], actor_id="human-admin")

    with pytest.raises(AgentApprovalError) as exc:
        _execute(service, row["id"], agent_id="agent-2")

    assert exc.value.code == "approval_actor_mismatch"
    assert exc.value.status_code == 403
    assert store.get_approval(row["id"])["executed_at"] is None


def test_execution_rechecks_current_authorization(context):
    service, store, _ = context
    row = _request(service)
    service.approve(row["id"], actor_id="human-admin")

    with pytest.raises(AgentApprovalError) as exc:
        _execute(service, row["id"], authorization_allowed=False)

    assert exc.value.code == "approval_not_authorized"
    assert store.get_approval(row["id"])["executed_at"] is None
