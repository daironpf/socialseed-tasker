"""Backend authorization for individual agent actions (issue #615)."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from socialseed_tasker.domain.agent_permissions import AGENT_RESOURCE_SCOPES
from socialseed_tasker.domain.agent_policy import resolve_effective_permissions

logger = logging.getLogger(__name__)

_AGENT_ACTIONS = frozenset({"read", "propose", "apply"})


class AgentProfileReader(Protocol):
    def get_profile(self, user_id: str) -> dict[str, Any] | None: ...


class AgentPermissionPolicyReader(Protocol):
    def list_for_context(
        self, *, organization_id: str | None = None, project_id: str | None = None
    ) -> list[dict[str, Any]]: ...

    def list_policies(
        self,
        *,
        scope_type: str | None = None,
        scope_id: str | None = None,
        is_active: bool | None = None,
    ) -> list[dict[str, Any]]: ...


@dataclass(frozen=True)
class AgentActionDecision:
    allowed: bool
    reason: str
    agent_id: str
    tool: str | None
    action: str
    resource_scope: str
    effective_permissions: dict[str, list[str]]


class AgentActionAuthorizer:
    """Loads current profile and policy data before each action decision."""

    def __init__(
        self,
        profiles: AgentProfileReader,
        policies: AgentPermissionPolicyReader,
        known_tools: Sequence[str],
    ) -> None:
        self._profiles = profiles
        self._policies = policies
        self._known_tools = tuple(known_tools)

    def authorize(
        self,
        *,
        agent_id: str,
        tool: str | None,
        action: str,
        resource_scope: str,
        project_id: str | None,
        organization_id: str | None = None,
    ) -> AgentActionDecision:
        reason = "denied"
        effective: dict[str, list[str]] = {
            "tools": [],
            "read_access": [],
            "propose_access": [],
            "apply_access": [],
        }

        if action not in _AGENT_ACTIONS:
            reason = "unknown_action"
        elif resource_scope not in AGENT_RESOURCE_SCOPES:
            reason = "unknown_resource_scope"
        elif tool is not None and tool not in self._known_tools:
            reason = "unknown_tool"
        elif not project_id:
            reason = "project_context_unresolved"
        else:
            profile = self._profiles.get_profile(agent_id)
            if profile is None:
                reason = "agent_not_found"
            else:
                organization_policies = self._policies.list_policies(
                    scope_type="organization",
                    is_active=True,
                )
                if organization_policies and not organization_id:
                    reason = "organization_context_unresolved"
                else:
                    applicable_policies = self._policies.list_for_context(
                        organization_id=organization_id,
                        project_id=project_id,
                    )
                    resolved = resolve_effective_permissions(
                        explicit={
                            field: profile.get(field) or []
                            for field in (
                                "tools",
                                "read_access",
                                "propose_access",
                                "apply_access",
                            )
                        },
                        enabled=bool(profile.get("enabled", True)),
                        policies=applicable_policies,
                        known_tools=self._known_tools,
                    )
                    effective = resolved.effective.as_dict()
                    action_scopes = {
                        "read": resolved.effective.read_access,
                        "propose": resolved.effective.propose_access,
                        "apply": resolved.effective.apply_access,
                    }
                    if not resolved.profile_enabled:
                        reason = "agent_disabled"
                    elif resolved.status != "resolved":
                        reason = "permissions_unresolved"
                    elif tool is not None and tool not in resolved.effective.tools:
                        reason = "tool_not_permitted"
                    elif resource_scope not in action_scopes.get(action, ()):
                        reason = "resource_scope_not_permitted"
                    else:
                        reason = "allowed"

        decision = AgentActionDecision(
            allowed=reason == "allowed",
            reason=reason,
            agent_id=agent_id,
            tool=tool,
            action=action,
            resource_scope=resource_scope,
            effective_permissions=effective,
        )
        log = logger.info if decision.allowed else logger.warning
        log(
            "Agent action %s: agent=%s tool=%s action=%s scope=%s reason=%s",
            "allowed" if decision.allowed else "denied",
            agent_id,
            tool or "-",
            action,
            resource_scope,
            reason,
        )
        return decision
