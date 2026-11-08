"""Typed execution limits, composition and server-side enforcement (issue #617)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from socialseed_tasker.application.agent_limits import (
    AgentLimitError,
    AgentLimitGuard,
    usage_from_run,
)
from socialseed_tasker.domain.agent_limits import (
    AgentLimits,
    AgentUsage,
    first_limit_violation,
    merge_agent_limits,
    parse_agent_limits,
    resolve_agent_limits,
)

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


class FakeRunStore:
    def __init__(self, **run: Any) -> None:
        self.run: dict[str, Any] = {
            "id": "run-1",
            "status": "running",
            "started_at": NOW,
            "total_tokens": 0,
            "total_tool_calls": 0,
            "total_cost_usd": 0.0,
            "duration_ms": None,
            **run,
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


def test_parse_accepts_canonical_and_legacy_aliases():
    parsed = parse_agent_limits(
        {
            "maxTokensPerRun": 100,
            "maxCostPerRun": 0.25,
            "timeoutSeconds": 30,
            "maxStepsPerRun": 5,
            "maxRisk": "low",
        }
    )

    assert parsed.as_dict() == {
        "max_tokens_per_run": 100,
        "max_cost_usd_per_run": 0.25,
        "max_duration_seconds": 30,
        "max_tool_calls_per_run": 5,
        "max_risk": "LOW",
    }


def test_parse_rejects_conflicting_aliases_and_invalid_values():
    with pytest.raises(ValueError):
        parse_agent_limits({"max_tokens": 10, "maxTokensPerRun": 20})
    with pytest.raises(ValueError):
        parse_agent_limits({"max_duration_seconds": 0})
    with pytest.raises(ValueError):
        parse_agent_limits({"max_risk": "CRITICAL"})


def test_merge_applies_the_most_restrictive_limit():
    merged = merge_agent_limits(
        AgentLimits(max_tokens_per_run=1000, max_duration_seconds=120, max_risk="HIGH"),
        AgentLimits(max_tokens_per_run=500, max_cost_usd_per_run=1.5, max_risk="MEDIUM"),
        AgentLimits(max_tool_calls_per_run=8),
    )

    assert merged.max_tokens_per_run == 500
    assert merged.max_cost_usd_per_run == 1.5
    assert merged.max_duration_seconds == 120
    assert merged.max_tool_calls_per_run == 8
    assert merged.max_risk == "MEDIUM"


def test_resolve_limits_marks_invalid_policy_documents_as_errors():
    resolved = resolve_agent_limits(
        {"max_tokens_per_run": 1000},
        [
            {"id": "p1", "is_active": True, "limits": {"max_tokens_per_run": 100}},
            {"id": "p2", "is_active": False, "limits": {"max_tokens_per_run": "bad"}},
            {"id": "p3", "is_active": True, "limits": {"max_risk": "NOPE"}},
        ],
    )

    assert resolved.limits.max_tokens_per_run == 100
    assert resolved.errors == ("policy:p3:max_risk",)


def test_first_limit_violation_reports_reached_limit_and_metadata():
    violation = first_limit_violation(
        AgentLimits(max_tool_calls_per_run=3),
        AgentUsage(tool_calls=3),
    )

    assert violation is not None
    assert violation.field == "max_tool_calls_per_run"
    assert violation.unit == "tool calls"
    assert violation.as_metadata() == {
        "limit": "max_tool_calls_per_run",
        "unit": "tool calls",
        "limit_value": 3,
        "observed": 3,
        "reason": "agent_limit_exceeded",
    }


def test_usage_from_open_run_measures_elapsed_time():
    usage = usage_from_run(
        {
            "started_at": (NOW - timedelta(seconds=40)).isoformat(),
            "total_tokens": 12,
            "total_tool_calls": 2,
            "total_cost_usd": 0.5,
        }
    )

    assert usage.tokens == 12
    assert usage.tool_calls == 2
    assert usage.cost_usd == 0.5
    assert usage.elapsed_seconds >= 39


def test_consume_tool_call_allows_n_actions_then_stops_the_run():
    store = FakeRunStore()
    guard = AgentLimitGuard(store)
    limits = AgentLimits(max_tool_calls_per_run=2)

    guard.consume_tool_call("run-1", limits)
    guard.consume_tool_call("run-1", limits)

    with pytest.raises(AgentLimitError) as raised:
        guard.consume_tool_call("run-1", limits)

    assert raised.value.violation.field == "max_tool_calls_per_run"
    assert raised.value.violation.observed == 2
    assert store.run["status"] == "failed"
    assert store.violations[0]["limit"] == "max_tool_calls_per_run"


def test_record_usage_stops_the_run_when_token_or_cost_limit_is_reached():
    store = FakeRunStore()
    guard = AgentLimitGuard(store)

    with pytest.raises(AgentLimitError):
        guard.record_usage_and_check(
            "run-1", AgentLimits(max_tokens_per_run=100), tokens=120
        )

    assert store.run["total_tokens"] == 120
    assert store.run["status"] == "failed"
    assert store.violations[-1]["observed"] == 120

    cost_store = FakeRunStore()
    with pytest.raises(AgentLimitError):
        AgentLimitGuard(cost_store).record_usage_and_check(
            "run-1", AgentLimits(max_cost_usd_per_run=0.5), cost_usd=0.75
        )
    assert cost_store.violations[-1]["limit"] == "max_cost_usd_per_run"


def test_check_without_limits_never_creates_a_quota():
    store = FakeRunStore(total_tokens=10_000, total_tool_calls=500)
    run = AgentLimitGuard(store).check("run-1", AgentLimits())

    assert run["status"] == "running"
    assert store.violations == []


def test_duration_limit_stops_an_open_run():
    store = FakeRunStore(started_at=NOW - timedelta(minutes=2))
    guard = AgentLimitGuard(store)

    with pytest.raises(AgentLimitError) as raised:
        guard.check("run-1", AgentLimits(max_duration_seconds=60))

    assert raised.value.violation.field == "max_duration_seconds"
    assert store.run["status"] == "failed"
