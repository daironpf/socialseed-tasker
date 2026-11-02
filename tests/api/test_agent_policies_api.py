"""API tests for inherited agent permissions (issue #613)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import psycopg
import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from socialseed_tasker.infrastructure.web_api.routers import agent_profiles
from socialseed_tasker.infrastructure.web_api.schemas import AgentPermissionPolicyCreate

PROFILE: dict[str, Any] = {
    "id": "agent-1",
    "username": "bot-qa",
    "email": "bot@socialseed.com",
    "avatar": None,
    "model": "gpt-4o",
    "specialization": "qa",
    "temperature": 0.2,
    "system_prompt": "You are a QA bot.",
    "tools": ["fs_read", "test_runner"],
    "read_access": ["repository", "issues", "tests"],
    "write_access": ["issues"],
    "propose_access": ["repository"],
    "apply_access": ["tests"],
    "limits": {"max_tokens": 4000},
    "enabled": True,
    "skills": ["Testing"],
    "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    "last_used_at": None,
}


class FakeProfileStore:
    def __init__(self, profiles: dict[str, dict[str, Any]]) -> None:
        self.profiles = profiles

    def get_profile(self, user_id: str) -> dict[str, Any] | None:
        return self.profiles.get(user_id)


class FakePolicyStore:
    def __init__(self, policies: list[dict[str, Any]] | None = None) -> None:
        self.policies = policies or []
        self.context: dict[str, str | None] = {}
        self.created: dict[str, Any] | None = None
        self.deleted: str | None = None

    def list_for_context(
        self, *, organization_id: str | None = None, project_id: str | None = None
    ) -> list[dict[str, Any]]:
        self.context = {
            "organization_id": organization_id,
            "project_id": project_id,
        }
        return self.policies

    def create_policy(self, **kwargs: Any) -> dict[str, Any]:
        self.created = kwargs
        return {
            "id": "policy-1",
            "name": kwargs["name"],
            "scope_type": kwargs["scope_type"],
            "scope_id": kwargs["scope_id"],
            "tools": kwargs.get("tools"),
            "read_access": kwargs.get("read_access"),
            "propose_access": kwargs.get("propose_access"),
            "apply_access": kwargs.get("apply_access"),
            "is_active": kwargs.get("is_active", True),
            "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        }

    def list_policies(self, **kwargs: Any) -> list[dict[str, Any]]:
        return self.policies

    def delete_policy(self, policy_id: str) -> bool:
        self.deleted = policy_id
        return policy_id == "policy-1"


class UnavailablePolicyStore:
    def list_for_context(self, **kwargs: Any) -> list[dict[str, Any]]:
        raise psycopg.OperationalError("down")

    def create_policy(self, **kwargs: Any) -> dict[str, Any]:
        raise psycopg.OperationalError("down")

    def list_policies(self, **kwargs: Any) -> list[dict[str, Any]]:
        raise psycopg.OperationalError("down")

    def delete_policy(self, policy_id: str) -> bool:
        raise psycopg.OperationalError("down")


def _install(
    monkeypatch: pytest.MonkeyPatch,
    *,
    profile: dict[str, Any] | None = PROFILE,
    policy_store: Any | None = None,
) -> FakePolicyStore:
    profiles = {} if profile is None else {profile["id"]: profile}
    monkeypatch.setattr(agent_profiles, "_pg_store", lambda: FakeProfileStore(profiles))
    fake_policies = policy_store or FakePolicyStore()
    monkeypatch.setattr(agent_profiles, "_permission_policy_store", lambda: fake_policies)
    return fake_policies


def test_effective_permissions_distinguish_explicit_inherited_and_effective(
    monkeypatch: pytest.MonkeyPatch,
):
    policies = FakePolicyStore(
        [
            {
                "id": "org-policy",
                "name": "Org ceiling",
                "scope_type": "organization",
                "scope_id": "org-1",
                "tools": ["fs_read"],
                "read_access": ["repository", "tests"],
                "propose_access": None,
                "apply_access": None,
                "is_active": True,
            },
            {
                "id": "project-policy",
                "name": "Project ceiling",
                "scope_type": "project",
                "scope_id": "proj-1",
                "tools": None,
                "read_access": ["repository"],
                "propose_access": ["repository"],
                "apply_access": None,
                "is_active": True,
            },
        ]
    )
    _install(monkeypatch, policy_store=policies)

    response = agent_profiles.get_effective_agent_permissions(
        "agent-1", organization_id="org-1", project_id="proj-1"
    )

    assert policies.context == {
        "organization_id": "org-1",
        "project_id": "proj-1",
    }
    assert response.data.status == "resolved"
    assert response.data.explicit.read_access == ["repository", "issues", "tests"]
    assert response.data.inherited.read_access == ["repository"]
    assert response.data.inherited.propose_access == ["repository"]
    assert response.data.inherited.apply_access is None
    assert response.data.effective.read_access == ["repository"]
    assert response.data.effective.tools == ["fs_read"]
    assert response.data.effective.propose_access == ["repository"]
    assert response.data.effective.apply_access == ["tests"]
    assert [source.id for source in response.data.sources] == [
        "org-policy",
        "project-policy",
    ]


def test_effective_permissions_without_context_do_not_inherit(
    monkeypatch: pytest.MonkeyPatch,
):
    policies = _install(monkeypatch)

    response = agent_profiles.get_effective_agent_permissions("agent-1")

    assert policies.context == {"organization_id": None, "project_id": None}
    assert response.data.inherited.read_access is None
    assert response.data.effective.read_access == ["repository", "issues", "tests"]


def test_unresolved_policy_fails_closed(monkeypatch: pytest.MonkeyPatch):
    _install(
        monkeypatch,
        policy_store=FakePolicyStore(
            [
                {
                    "id": "broken",
                    "name": "Broken",
                    "scope_type": "project",
                    "scope_id": "proj-1",
                    "read_access": ["secrets"],
                    "is_active": True,
                }
            ]
        ),
    )

    response = agent_profiles.get_effective_agent_permissions(
        "agent-1", project_id="proj-1"
    )

    assert response.data.status == "unresolved"
    assert response.data.effective.tools == []
    assert response.data.effective.read_access == []
    assert response.data.effective.propose_access == []
    assert response.data.effective.apply_access == []
    assert response.data.errors == ["policy:broken:resource:secrets"]


def test_disabled_profile_has_no_effective_permissions(
    monkeypatch: pytest.MonkeyPatch,
):
    disabled = {**PROFILE, "enabled": False}
    _install(monkeypatch, profile=disabled)

    response = agent_profiles.get_effective_agent_permissions("agent-1")

    assert response.data.profile_enabled is False
    assert response.data.explicit.read_access == ["repository", "issues", "tests"]
    assert response.data.effective.read_access == []
    assert response.data.effective.tools == []


def test_effective_permissions_404_for_unknown_agent(
    monkeypatch: pytest.MonkeyPatch,
):
    _install(monkeypatch, profile=None)

    with pytest.raises(HTTPException) as exc:
        agent_profiles.get_effective_agent_permissions("missing")

    assert exc.value.status_code == 404


def test_unavailable_policy_source_returns_503(
    monkeypatch: pytest.MonkeyPatch,
):
    _install(monkeypatch, policy_store=UnavailablePolicyStore())

    with pytest.raises(HTTPException) as exc:
        agent_profiles.get_effective_agent_permissions(
            "agent-1", project_id="proj-1"
        )

    assert exc.value.status_code == 503


def test_create_permission_policy_normalizes_fields(
    monkeypatch: pytest.MonkeyPatch,
):
    policies = _install(monkeypatch)
    body = AgentPermissionPolicyCreate(
        name="Project ceiling",
        scope_type="project",
        scope_id="proj-1",
        tools=[" fs_read ", "fs_read"],
        read_access=[" repository ", "repository"],
        propose_access=[],
        apply_access=None,
    )

    response = agent_profiles.create_agent_permission_policy(body)

    assert policies.created is not None
    assert policies.created["tools"] == ["fs_read"]
    assert policies.created["read_access"] == ["repository"]
    assert policies.created["propose_access"] == []
    assert policies.created["apply_access"] is None
    assert response.data.id == "policy-1"
    assert response.data.scope_type == "project"


def test_create_permission_policy_rejects_unknown_resource():
    with pytest.raises(ValidationError):
        AgentPermissionPolicyCreate(
            name="Bad",
            scope_type="project",
            scope_id="proj-1",
            read_access=["secrets"],
        )


def test_create_permission_policy_maps_unknown_tool_to_422(
    monkeypatch: pytest.MonkeyPatch,
):
    class RejectingStore(FakePolicyStore):
        def create_policy(self, **kwargs: Any) -> dict[str, Any]:
            raise ValueError("tool:shell")

    _install(monkeypatch, policy_store=RejectingStore())

    with pytest.raises(HTTPException) as exc:
        agent_profiles.create_agent_permission_policy(
            AgentPermissionPolicyCreate(
                name="Bad",
                scope_type="project",
                scope_id="proj-1",
                tools=["shell"],
            )
        )

    assert exc.value.status_code == 422
    assert exc.value.detail == "unknown tool: shell"


def test_create_permission_policy_unavailable_returns_503(
    monkeypatch: pytest.MonkeyPatch,
):
    _install(monkeypatch, policy_store=UnavailablePolicyStore())

    with pytest.raises(HTTPException) as exc:
        agent_profiles.create_agent_permission_policy(
            AgentPermissionPolicyCreate(
                name="Policy",
                scope_type="organization",
                scope_id="org-1",
            )
        )

    assert exc.value.status_code == 503


def test_list_and_delete_permission_policies(monkeypatch: pytest.MonkeyPatch):
    policies = _install(
        monkeypatch,
        policy_store=FakePolicyStore(
            [
                {
                    "id": "policy-1",
                    "name": "Project ceiling",
                    "scope_type": "project",
                    "scope_id": "proj-1",
                    "tools": None,
                    "read_access": ["repository"],
                    "propose_access": None,
                    "apply_access": None,
                    "is_active": True,
                    "created_at": None,
                }
            ]
        ),
    )

    listed = agent_profiles.list_agent_permission_policies(scope_type="project")
    deleted = agent_profiles.delete_agent_permission_policy("policy-1")

    assert [item.id for item in listed.data] == ["policy-1"]
    assert deleted.data is True
    assert policies.deleted == "policy-1"


def test_delete_permission_policy_404(monkeypatch: pytest.MonkeyPatch):
    _install(monkeypatch)

    with pytest.raises(HTTPException) as exc:
        agent_profiles.delete_agent_permission_policy("missing")

    assert exc.value.status_code == 404
