"""Policy inheritance and precedence for agent permissions (issue #613).

Organization and project policies are ceilings, never grants. The effective
permission set is the profile's explicit set intersected with every applicable
ceiling; a higher policy can therefore restrict a profile but never widen it.
An absent ceiling means "no extra restriction", while an empty ceiling denies
that capability completely.

Policy sources and malformed documents are evaluated fail-closed: if an active
policy cannot be interpreted, the result is ``unresolved`` and every effective
capability is empty.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from socialseed_tasker.domain.agent_permissions import (
    normalize_resource_scopes,
    normalize_tool_slugs,
)

POLICY_SCOPES: tuple[str, ...] = ("organization", "project")
CAPABILITY_FIELDS: tuple[str, ...] = (
    "tools",
    "read_access",
    "propose_access",
    "apply_access",
)

EvaluationStatus = Literal["resolved", "unresolved"]


@dataclass(frozen=True)
class PermissionSet:
    """A concrete set of capabilities granted to an agent."""

    tools: tuple[str, ...] = ()
    read_access: tuple[str, ...] = ()
    propose_access: tuple[str, ...] = ()
    apply_access: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, list[str]]:
        return {
            "tools": list(self.tools),
            "read_access": list(self.read_access),
            "propose_access": list(self.propose_access),
            "apply_access": list(self.apply_access),
        }

    def restricted_to(self, limits: PermissionLimits) -> PermissionSet:
        return PermissionSet(
            tools=_intersect(self.tools, limits.tools),
            read_access=_intersect(self.read_access, limits.read_access),
            propose_access=_intersect(self.propose_access, limits.propose_access),
            apply_access=_intersect(self.apply_access, limits.apply_access),
        )


@dataclass(frozen=True)
class PermissionLimits:
    """Per-capability ceilings; ``None`` means the policy is silent."""

    tools: tuple[str, ...] | None = None
    read_access: tuple[str, ...] | None = None
    propose_access: tuple[str, ...] | None = None
    apply_access: tuple[str, ...] | None = None

    def as_dict(self) -> dict[str, list[str] | None]:
        return {
            "tools": None if self.tools is None else list(self.tools),
            "read_access": None if self.read_access is None else list(self.read_access),
            "propose_access": (
                None if self.propose_access is None else list(self.propose_access)
            ),
            "apply_access": (
                None if self.apply_access is None else list(self.apply_access)
            ),
        }

    def intersect(self, other: PermissionLimits) -> PermissionLimits:
        return PermissionLimits(
            tools=_merge_limit(self.tools, other.tools),
            read_access=_merge_limit(self.read_access, other.read_access),
            propose_access=_merge_limit(self.propose_access, other.propose_access),
            apply_access=_merge_limit(self.apply_access, other.apply_access),
        )


@dataclass(frozen=True)
class PolicySource:
    """A policy that participated in the effective decision."""

    id: str
    name: str
    scope: str
    scope_id: str


@dataclass(frozen=True)
class EffectivePermissions:
    """Explicit, inherited and effective capabilities for one agent context."""

    status: EvaluationStatus
    profile_enabled: bool
    explicit: PermissionSet
    inherited: PermissionLimits
    effective: PermissionSet
    sources: tuple[PolicySource, ...] = ()
    errors: tuple[str, ...] = ()


def resolve_effective_permissions(
    *,
    explicit: Mapping[str, Iterable[str]],
    enabled: bool,
    policies: Sequence[Mapping[str, Any]],
    known_tools: Iterable[str] | None = None,
) -> EffectivePermissions:
    """Intersect profile permissions with the applicable policy ceilings.

    ``policies`` accepts the storage rows shaped as ``scope_type``,
    ``scope_id``, ``tools``, ``read_access``, ``propose_access``,
    ``apply_access``, ``is_active`` and optional ``id``/``name``. Inactive
    policies are ignored. Active policies with an invalid scope, capability or
    document mark the result ``unresolved``; callers must treat that as a
    denial (no effective capabilities).
    """
    tool_universe = frozenset(known_tools) if known_tools is not None else None
    errors: list[str] = []

    try:
        profile = _parse_explicit(explicit, tool_universe)
    except ValueError as exc:
        profile = PermissionSet()
        errors.append(f"profile:{exc}")

    inherited = PermissionLimits()
    sources: list[PolicySource] = []
    for raw in policies:
        policy_id = str(raw.get("id") or "<unknown>")
        if not raw.get("is_active", True):
            continue
        scope = str(raw.get("scope_type") or raw.get("scope") or "").strip().lower()
        if scope not in POLICY_SCOPES:
            errors.append(f"policy:{policy_id}:scope")
            continue
        scope_id = str(raw.get("scope_id") or "").strip()
        if not scope_id:
            errors.append(f"policy:{policy_id}:scope_id")
            continue
        try:
            limits = _parse_limits(raw, tool_universe)
        except ValueError as exc:
            errors.append(f"policy:{policy_id}:{exc}")
            continue
        inherited = inherited.intersect(limits)
        sources.append(
            PolicySource(
                id=policy_id,
                name=str(raw.get("name") or policy_id),
                scope=scope,
                scope_id=scope_id,
            )
        )

    effective = (
        PermissionSet() if errors or not enabled else profile.restricted_to(inherited)
    )

    return EffectivePermissions(
        status="unresolved" if errors else "resolved",
        profile_enabled=bool(enabled),
        explicit=profile,
        inherited=inherited,
        effective=effective,
        sources=tuple(sources),
        errors=tuple(errors),
    )


def _parse_explicit(
    explicit: Mapping[str, Iterable[str]], known_tools: frozenset[str] | None
) -> PermissionSet:
    return PermissionSet(
        tools=tuple(_normalize_capability("tools", explicit.get("tools") or [], known_tools)),
        read_access=tuple(
            _normalize_capability("read_access", explicit.get("read_access") or [], known_tools)
        ),
        propose_access=tuple(
            _normalize_capability(
                "propose_access", explicit.get("propose_access") or [], known_tools
            )
        ),
        apply_access=tuple(
            _normalize_capability("apply_access", explicit.get("apply_access") or [], known_tools)
        ),
    )


def _parse_limits(
    raw: Mapping[str, Any], known_tools: frozenset[str] | None
) -> PermissionLimits:
    def limit(field: str) -> tuple[str, ...] | None:
        if field not in raw or raw[field] is None:
            return None
        value = raw[field]
        if isinstance(value, (str, bytes)) or not isinstance(value, Iterable):
            raise ValueError(field)
        return tuple(_normalize_capability(field, value, known_tools))

    return PermissionLimits(
        tools=limit("tools"),
        read_access=limit("read_access"),
        propose_access=limit("propose_access"),
        apply_access=limit("apply_access"),
    )


def _normalize_capability(
    field: str, values: Iterable[str], known_tools: frozenset[str] | None
) -> list[str]:
    if isinstance(values, (str, bytes)):
        raise ValueError(field)
    if field == "tools":
        return normalize_tool_slugs(values, known_tools)
    return normalize_resource_scopes(values)


def _merge_limit(
    left: tuple[str, ...] | None, right: tuple[str, ...] | None
) -> tuple[str, ...] | None:
    if left is None and right is None:
        return None
    if left is None:
        return tuple(sorted(set(right or ())))
    if right is None:
        return tuple(sorted(set(left)))
    return tuple(sorted(set(left) & set(right)))


def _intersect(
    values: tuple[str, ...], ceiling: tuple[str, ...] | None
) -> tuple[str, ...]:
    if ceiling is None:
        return values
    allowed = set(ceiling)
    return tuple(value for value in values if value in allowed)
