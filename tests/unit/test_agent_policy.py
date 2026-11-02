"""Unit tests for inherited agent permissions (issue #613)."""

from __future__ import annotations

from typing import Any

from socialseed_tasker.domain.agent_policy import (
    EffectivePermissions,
    PermissionLimits,
    PermissionSet,
    resolve_effective_permissions,
)

KNOWN_TOOLS = {"fs_read", "fs_write", "test_runner", "git_tools"}


def _policy(
    *,
    policy_id: str = "p1",
    scope: str = "project",
    scope_id: str = "proj-1",
    is_active: bool = True,
    **capabilities: Any,
) -> dict[str, Any]:
    return {
        "id": policy_id,
        "name": f"policy-{policy_id}",
        "scope_type": scope,
        "scope_id": scope_id,
        "is_active": is_active,
        **capabilities,
    }


def _resolve(
    explicit: dict[str, list[str]] | None = None,
    policies: list[dict[str, Any]] | None = None,
    *,
    enabled: bool = True,
) -> EffectivePermissions:
    return resolve_effective_permissions(
        explicit=explicit
        or {
            "tools": ["fs_read", "test_runner"],
            "read_access": ["repository", "issues", "tests"],
            "propose_access": ["repository"],
            "apply_access": ["tests"],
        },
        enabled=enabled,
        policies=policies or [],
        known_tools=KNOWN_TOOLS,
    )


def test_no_policy_keeps_explicit_permissions_and_reports_no_inherited_ceiling():
    result = _resolve()

    assert result.status == "resolved"
    assert result.effective == result.explicit
    assert result.inherited == PermissionLimits()
    assert result.sources == ()
    assert result.errors == ()


def test_project_ceiling_restricts_profile_and_preserves_explicit_order():
    result = _resolve(
        policies=[
            _policy(
                tools=["fs_read", "test_runner"],
                read_access=["tests", "repository"],
                propose_access=[],
                apply_access=["tests"],
            )
        ]
    )

    assert result.status == "resolved"
    assert result.explicit.read_access == ("repository", "issues", "tests")
    assert result.inherited.read_access == ("repository", "tests")
    assert result.effective.read_access == ("repository", "tests")
    assert result.effective.tools == ("fs_read", "test_runner")
    assert result.effective.propose_access == ()
    assert result.effective.apply_access == ("tests",)
    assert [source.scope for source in result.sources] == ["project"]


def test_organization_and_project_ceilings_intersect():
    result = _resolve(
        policies=[
            _policy(
                policy_id="org",
                scope="organization",
                scope_id="org-1",
                tools=["fs_read", "test_runner"],
                read_access=["repository", "issues", "tests"],
            ),
            _policy(
                policy_id="proj",
                scope="project",
                scope_id="proj-1",
                tools=["fs_read"],
                read_access=["repository", "tests"],
            ),
        ]
    )

    assert result.inherited.tools == ("fs_read",)
    assert result.inherited.read_access == ("repository", "tests")
    assert result.effective.tools == ("fs_read",)
    assert result.effective.read_access == ("repository", "tests")
    assert [source.id for source in result.sources] == ["org", "proj"]


def test_profile_cannot_widen_a_higher_policy():
    result = _resolve(
        explicit={
            "tools": ["fs_write"],
            "read_access": ["issues"],
            "propose_access": [],
            "apply_access": [],
        },
        policies=[
            _policy(
                tools=["fs_read"],
                read_access=["repository"],
                propose_access=["repository"],
                apply_access=[],
            )
        ],
    )

    assert result.effective == PermissionSet()
    assert result.inherited.tools == ("fs_read",)


def test_empty_ceiling_denies_the_capability():
    result = _resolve(policies=[_policy(read_access=[], apply_access=[])])

    assert result.inherited.read_access == ()
    assert result.effective.read_access == ()
    assert result.effective.apply_access == ()
    assert result.effective.tools == ("fs_read", "test_runner")


def test_silent_capability_is_not_restricted():
    result = _resolve(policies=[_policy(tools=["fs_read"])])

    assert result.inherited.tools == ("fs_read",)
    assert result.inherited.read_access is None
    assert result.effective.read_access == ("repository", "issues", "tests")


def test_unknown_policy_scope_is_unresolved_and_denies_everything():
    result = _resolve(policies=[_policy(scope="tenant", read_access=["repository"])])

    assert result.status == "unresolved"
    assert result.effective == PermissionSet()
    assert result.errors == ("policy:p1:scope",)


def test_missing_scope_id_is_unresolved():
    result = _resolve(policies=[_policy(scope_id=" ")])

    assert result.status == "unresolved"
    assert result.effective == PermissionSet()
    assert result.errors == ("policy:p1:scope_id",)


def test_unknown_resource_in_policy_is_unresolved():
    result = _resolve(policies=[_policy(read_access=["secrets"])])

    assert result.status == "unresolved"
    assert result.effective == PermissionSet()
    assert result.errors == ("policy:p1:resource:secrets",)


def test_unknown_tool_in_policy_is_unresolved():
    result = _resolve(policies=[_policy(tools=["shell"])])

    assert result.status == "unresolved"
    assert result.effective == PermissionSet()
    assert result.errors == ("policy:p1:tool:shell",)


def test_malformed_policy_document_is_unresolved():
    policy = _policy()
    policy["read_access"] = "repository"

    result = _resolve(policies=[policy])

    assert result.status == "unresolved"
    assert result.effective == PermissionSet()
    assert result.errors == ("policy:p1:read_access",)


def test_inactive_policy_is_ignored_without_evaluation():
    result = _resolve(
        policies=[_policy(is_active=False, scope="unknown", read_access=["secrets"])]
    )

    assert result.status == "resolved"
    assert result.effective == result.explicit
    assert result.sources == ()


def test_disabled_profile_denies_every_effective_capability():
    result = _resolve(enabled=False, policies=[_policy(read_access=["repository"])])

    assert result.status == "resolved"
    assert result.profile_enabled is False
    assert result.effective == PermissionSet()
    assert result.explicit.read_access == ("repository", "issues", "tests")


def test_policy_lists_are_trimmed_and_deduplicated():
    result = _resolve(
        policies=[
            _policy(
                tools=[" fs_read ", "fs_read"],
                read_access=[" repository ", "repository", "tests"],
            )
        ]
    )

    assert result.inherited.tools == ("fs_read",)
    assert result.inherited.read_access == ("repository", "tests")


def test_permission_dicts_are_json_ready():
    result = _resolve()

    assert result.explicit.as_dict()["read_access"] == [
        "repository",
        "issues",
        "tests",
    ]
    assert result.inherited.as_dict()["read_access"] is None
