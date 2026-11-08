"""Typed execution limits for agents (issue #617).

A limit declares a value, a unit, the scope it applies to (one run) and the
behaviour when it is reached: no new action may start. Limits come from the
agent profile and from organization/project policies; a policy can only make a
profile limit stricter, never relax it. An absent limit means "no configured
ceiling", not an implicit quota.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

AGENT_LIMIT_UNITS: dict[str, str] = {
    "max_tokens_per_run": "tokens",
    "max_cost_usd_per_run": "USD",
    "max_duration_seconds": "seconds",
    "max_tool_calls_per_run": "tool calls",
}

AGENT_LIMIT_RISK_ORDER: dict[str, int] = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}

# Canonical field -> accepted aliases. The camelCase aliases keep the Studio's
# existing profile payloads working; storage always uses canonical snake_case.
_LIMIT_ALIASES: dict[str, tuple[str, ...]] = {
    "max_tokens_per_run": ("max_tokens_per_run", "maxTokensPerRun", "max_tokens"),
    "max_cost_usd_per_run": (
        "max_cost_usd_per_run",
        "maxCostUsdPerRun",
        "maxCostPerRun",
        "max_cost_usd",
    ),
    "max_duration_seconds": (
        "max_duration_seconds",
        "maxDurationSeconds",
        "maxDuration",
        "timeoutSeconds",
        "max_duration",
    ),
    "max_tool_calls_per_run": (
        "max_tool_calls_per_run",
        "maxToolCallsPerRun",
        "maxStepsPerRun",
        "max_tool_calls",
        "max_steps",
    ),
    "max_risk": ("max_risk", "maxRisk"),
}

_VIOLATION_ORDER: tuple[str, ...] = (
    "max_tool_calls_per_run",
    "max_duration_seconds",
    "max_tokens_per_run",
    "max_cost_usd_per_run",
)


@dataclass(frozen=True)
class AgentLimits:
    """Effective limits for one agent run (``None`` = not configured)."""

    max_tokens_per_run: int | None = None
    max_cost_usd_per_run: float | None = None
    max_duration_seconds: int | None = None
    max_tool_calls_per_run: int | None = None
    max_risk: str | None = None

    def as_dict(self) -> dict[str, Any]:
        """Canonical snake_case representation, omitting unset limits."""
        values = {
            "max_tokens_per_run": self.max_tokens_per_run,
            "max_cost_usd_per_run": self.max_cost_usd_per_run,
            "max_duration_seconds": self.max_duration_seconds,
            "max_tool_calls_per_run": self.max_tool_calls_per_run,
            "max_risk": self.max_risk,
        }
        return {key: value for key, value in values.items() if value is not None}

    def is_empty(self) -> bool:
        return not self.as_dict()


@dataclass(frozen=True)
class AgentUsage:
    """Server-measured consumption of one run."""

    tokens: int = 0
    cost_usd: float = 0.0
    tool_calls: int = 0
    elapsed_seconds: float = 0.0


@dataclass(frozen=True)
class AgentLimitViolation:
    """A limit that was reached, with enough context to report the stop reason."""

    field: str
    limit: int | float
    observed: int | float

    @property
    def unit(self) -> str:
        return AGENT_LIMIT_UNITS.get(self.field, "units")

    @property
    def message(self) -> str:
        return (
            f"{self.field} reached ({self.observed:g}/{self.limit:g} {self.unit}); "
            "the run cannot start new actions"
        )

    def as_metadata(self) -> dict[str, Any]:
        return {
            "limit": self.field,
            "unit": self.unit,
            "limit_value": self.limit,
            "observed": self.observed,
            "reason": "agent_limit_exceeded",
        }


@dataclass(frozen=True)
class ResolvedAgentLimits:
    """Effective limits plus the errors found while composing policy sources."""

    limits: AgentLimits
    errors: tuple[str, ...] = ()


def resolve_agent_limits(
    profile_limits: Mapping[str, Any] | None,
    policies: Mapping[str, Any] | None = None,
) -> ResolvedAgentLimits:
    """Compose the profile's limits with every applicable policy ceiling.

    ``policies`` accepts the stored policy rows (``id``/``name``/``is_active``
    and the JSONB ``limits`` document). An active policy with an invalid limits
    document yields an error so callers can fail closed; the merged value still
    contains the valid profile ceiling for display.
    """
    errors: list[str] = []
    parsed: list[AgentLimits] = []
    try:
        parsed.append(parse_agent_limits(profile_limits))
    except ValueError as exc:
        errors.append(f"profile:{exc}")

    for raw in policies or ():
        if not raw.get("is_active", True):
            continue
        policy_id = str(raw.get("id") or "<unknown>")
        try:
            parsed.append(parse_agent_limits(raw.get("limits")))
        except ValueError as exc:
            errors.append(f"policy:{policy_id}:{exc}")

    return ResolvedAgentLimits(limits=merge_agent_limits(*parsed), errors=tuple(errors))


def parse_agent_limits(raw: Mapping[str, Any] | None) -> AgentLimits:
    """Normalize a JSONB limits document, accepting camelCase aliases.

    Unknown keys are ignored so older records can carry presentation metadata;
    known keys with an invalid value raise ``ValueError`` (fail closed).
    """
    if raw is None:
        return AgentLimits()
    if not isinstance(raw, Mapping):
        raise ValueError("limits")

    values: dict[str, Any] = {}
    for field, aliases in _LIMIT_ALIASES.items():
        found = [(alias, raw[alias]) for alias in aliases if alias in raw and raw[alias] is not None]
        if not found:
            continue
        first_value = found[0][1]
        for _, candidate in found[1:]:
            if candidate != first_value:
                raise ValueError(f"{field}:ambiguous")
        values[field] = first_value

    return AgentLimits(
        max_tokens_per_run=_positive_int("max_tokens_per_run", values.get("max_tokens_per_run")),
        max_cost_usd_per_run=_positive_cost(values.get("max_cost_usd_per_run")),
        max_duration_seconds=_positive_int(
            "max_duration_seconds", values.get("max_duration_seconds")
        ),
        max_tool_calls_per_run=_positive_int(
            "max_tool_calls_per_run", values.get("max_tool_calls_per_run")
        ),
        max_risk=_risk(values.get("max_risk")),
    )


def merge_agent_limits(*limits: AgentLimits | None) -> AgentLimits:
    """Apply the most restrictive value from every source.

    Numeric ceilings take the minimum of the configured values; ``max_risk``
    takes the lowest allowed risk level. ``None`` sources are silent.
    """
    configured = [item for item in limits if item is not None]
    if not configured:
        return AgentLimits()

    def tightest_int(field: str) -> int | None:
        values = [getattr(item, field) for item in configured if getattr(item, field) is not None]
        return min(values) if values else None

    def tightest_cost() -> float | None:
        values = [
            item.max_cost_usd_per_run
            for item in configured
            if item.max_cost_usd_per_run is not None
        ]
        return min(values) if values else None

    risks = [item.max_risk for item in configured if item.max_risk is not None]
    tightest_risk = min(risks, key=lambda value: AGENT_LIMIT_RISK_ORDER[value]) if risks else None

    return AgentLimits(
        max_tokens_per_run=tightest_int("max_tokens_per_run"),
        max_cost_usd_per_run=tightest_cost(),
        max_duration_seconds=tightest_int("max_duration_seconds"),
        max_tool_calls_per_run=tightest_int("max_tool_calls_per_run"),
        max_risk=tightest_risk,
    )


def first_limit_violation(limits: AgentLimits, usage: AgentUsage) -> AgentLimitViolation | None:
    """Return the first reached limit in a deterministic, user-facing order."""
    observed = {
        "max_tool_calls_per_run": (limits.max_tool_calls_per_run, usage.tool_calls),
        "max_duration_seconds": (limits.max_duration_seconds, usage.elapsed_seconds),
        "max_tokens_per_run": (limits.max_tokens_per_run, usage.tokens),
        "max_cost_usd_per_run": (limits.max_cost_usd_per_run, usage.cost_usd),
    }
    for field in _VIOLATION_ORDER:
        limit, current = observed[field]
        if limit is not None and current >= limit:
            return AgentLimitViolation(field=field, limit=limit, observed=current)
    return None


def _positive_int(field: str, value: Any) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(field)
    if isinstance(value, float) and not value.is_integer():
        raise ValueError(field)
    integer = int(value)
    if integer <= 0:
        raise ValueError(field)
    return integer


def _positive_cost(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("max_cost_usd_per_run")
    cost = float(value)
    if cost <= 0:
        raise ValueError("max_cost_usd_per_run")
    return cost


def _risk(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("max_risk")
    risk = value.strip().upper()
    if risk not in AGENT_LIMIT_RISK_ORDER:
        raise ValueError("max_risk")
    return risk
