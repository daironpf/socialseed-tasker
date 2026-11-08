"""Tests for per-action agent authorization (issue #615)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from socialseed_tasker.application.agent_authorization import AgentActionAuthorizer
from socialseed_tasker.domain.entities import Component
from socialseed_tasker.infrastructure.web_api.agent_authorization import (
    resolve_component_project_id,
)


class FakeProfileStore:
    def __init__(self, profile: dict[str, Any] | None) -> None:
        self.profile = profile
        self.calls = 0

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        self.calls += 1
        return self.profile


class FakePolicyStore:
    def __init__(self, policies: list[dict[str, Any]] | None = None) -> None:
        self.policies = policies or []
        self.calls = 0

    def list_for_context(
        self, *, organization_id: str | None = None, project_id: str | None = None
    ) -> list[dict[str, Any]]:
        self.calls += 1
        return [
            policy
            for policy in self.policies
            if policy.get("scope_type") == "project"
            and policy.get("scope_id") == project_id
            and policy.get("is_active", True)
        ]

    def list_policies(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        is_active: bool | None = None,
    ) -> list[dict[str, Any]]:
        return [
            policy
            for policy in self.policies
            if (scope_type is None or policy.get("scope_type") == scope_type)
            and (scope_id is None or policy.get("scope_id") == scope_id)
            and (is_active is None or policy.get("is_active", True) == is_active)
        ]


PROFILE: dict[str, Any] = {
    "id": "agent-1",
    "enabled": True,
    "tools": ["neo4j_query", "fs_write"],
    "read_access": ["graph", "issues", "repository"],
    "propose_access": ["repository"],
    "apply_access": [],
}


def _authorizer(
    *,
    profile: dict[str, Any] | None = PROFILE,
    policies: list[dict[str, Any]] | None = None,
) -> tuple[AgentActionAuthorizer, FakeProfileStore, FakePolicyStore]:
    profiles = FakeProfileStore(profile)
    policy_store = FakePolicyStore(policies)
    return (
        AgentActionAuthorizer(
            profiles,
            policy_store,
            ["neo4j_query", "fs_write"],
        ),
        profiles,
        policy_store,
    )


def _authorize(
    authorizer: AgentActionAuthorizer,
    *,
    tool: str | None = "neo4j_query",
    action: str = "read",
    scope: str = "issues",
    project_id: str | None = "project-1",
):
    return authorizer.authorize(
        agent_id="agent-1",
        tool=tool,
        action=action,
        resource_scope=scope,
        project_id=project_id,
    )


def test_authorizes_current_profile_and_project_permissions():
    authorizer, profiles, policies = _authorizer()

    decision = _authorize(authorizer)

    assert decision.allowed is True
    assert decision.reason == "allowed"
    assert profiles.calls == 1
    assert policies.calls == 1


def test_policy_changes_apply_to_the_next_action():
    authorizer, _, policies = _authorizer()

    assert _authorize(authorizer).allowed is True
    policies.policies.append(
        {
            "id": "deny-issues",
            "scope_type": "project",
            "scope_id": "project-1",
            "is_active": True,
            "read_access": ["graph"],
        }
    )

    decision = _authorize(authorizer)

    assert decision.allowed is False
    assert decision.reason == "resource_scope_not_permitted"


def test_proposal_permission_does_not_grant_apply():
    authorizer, _, _ = _authorizer()

    proposal = _authorize(authorizer, tool="fs_write", action="propose", scope="repository")
    apply = _authorize(authorizer, tool="fs_write", action="apply", scope="repository")

    assert proposal.allowed is True
    assert apply.allowed is False
    assert apply.reason == "resource_scope_not_permitted"


def test_disabled_and_unknown_agents_are_denied():
    disabled = dict(PROFILE, enabled=False)
    authorizer, _, _ = _authorizer(profile=disabled)
    assert _authorize(authorizer).reason == "agent_disabled"

    authorizer, _, _ = _authorizer(profile=None)
    assert _authorize(authorizer).reason == "agent_not_found"


def test_unknown_tool_action_and_resource_are_denied():
    authorizer, _, _ = _authorizer()

    assert _authorize(authorizer, tool="unlisted").reason == "unknown_tool"
    assert _authorize(authorizer, action="delete").reason == "unknown_action"
    assert _authorize(authorizer, scope="secrets").reason == "unknown_resource_scope"


def test_missing_project_or_unresolved_organization_context_fails_closed():
    authorizer, _, _ = _authorizer()

    assert _authorize(authorizer, project_id=None).reason == "project_context_unresolved"

    authorizer, _, _ = _authorizer(
        policies=[
            {
                "id": "org-ceiling",
                "scope_type": "organization",
                "scope_id": "org-1",
                "is_active": True,
            }
        ]
    )
    assert _authorize(authorizer).reason == "organization_context_unresolved"


def test_project_context_is_derived_from_a_unique_backend_project_node():
    project_id = str(uuid4())

    class Repository:
        def list_project_nodes(self) -> list[dict[str, str]]:
            return [{"id": project_id, "name": "Store", "slug": "store"}]

    component = Component(name="API", project="Store")

    assert resolve_component_project_id(component, Repository()) == project_id


def test_project_context_denies_ambiguous_or_mismatched_backend_mapping():
    project_id = str(uuid4())
    other_project_id = str(uuid4())
    unknown_project_id = str(uuid4())

    class AmbiguousRepository:
        def list_project_nodes(self) -> list[dict[str, str]]:
            return [
                {"id": project_id, "name": "Store", "slug": "store"},
                {"id": other_project_id, "name": "Store", "slug": "store"},
            ]

    stale_component = Component(
        name="API",
        project="Store",
        project_id=unknown_project_id,
    )
    component = Component(name="API", project="Store")

    assert resolve_component_project_id(component, AmbiguousRepository()) is None
    assert resolve_component_project_id(stale_component, AmbiguousRepository()) is None

def test_effective_limits_compose_profile_with_the_tightest_policy():
    profile = {**PROFILE, "limits": {"max_tokens_per_run": 4000, "max_duration_seconds": 120}}
    policies = [
        {
            "id": "ceiling",
            "scope_type": "project",
            "scope_id": "project-1",
            "is_active": True,
            "limits": {"maxTokensPerRun": 1000, "max_steps": 3},
        }
    ]
    authorizer, _, _ = _authorizer(profile=profile, policies=policies)

    decision = _authorize(authorizer)

    assert decision.allowed is True
    assert decision.effective_limits.max_tokens_per_run == 1000
    assert decision.effective_limits.max_duration_seconds == 120
    assert decision.effective_limits.max_tool_calls_per_run == 3


def test_invalid_policy_limits_fail_closed():
    policies = [
        {
            "id": "broken",
            "scope_type": "project",
            "scope_id": "project-1",
            "is_active": True,
            "limits": {"max_tokens_per_run": 0},
        }
    ]
    authorizer, _, _ = _authorizer(policies=policies)

    decision = _authorize(authorizer)

    assert decision.allowed is False
    assert decision.reason == "permissions_unresolved"


def test_absence_of_limits_does_not_create_a_quota():
    authorizer, _, _ = _authorizer()

    decision = _authorize(authorizer)

    assert decision.allowed is True
    assert decision.effective_limits.is_empty() is True
