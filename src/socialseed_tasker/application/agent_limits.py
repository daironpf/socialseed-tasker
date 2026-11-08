"""Server-side measurement and enforcement of agent execution limits (#617).

The runtime reports token/cost consumption through a run-scoped execution
credential; the server keeps the authoritative counters in ``agent_runs`` and
decides whether another action may start. Client-supplied usage is never
trusted for enforcement.

When a limit is reached the guard atomically stops the run, appends a
``violation`` log with the limit metadata and raises :class:`AgentLimitError`, so
every caller reports the same reason and no further action starts.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Protocol

from socialseed_tasker.domain.agent_limits import (
    AgentLimitViolation,
    AgentLimits,
    AgentUsage,
    first_limit_violation,
)

logger = logging.getLogger(__name__)

AGENT_LIMIT_EXCEEDED = "agent_limit_exceeded"


class AgentLimitError(Exception):
    """Raised when an agent run has reached a configured limit.

    ``status_code`` lets the HTTP layer answer 409 while the metadata keeps the
    reached field, unit, limit and observed consumption for the UI and logs.
    """

    status_code = 409
    code = AGENT_LIMIT_EXCEEDED

    def __init__(self, violation: AgentLimitViolation, *, run_id: str | None = None) -> None:
        super().__init__(violation.message)
        self.violation = violation
        self.run_id = run_id

    @property
    def message(self) -> str:
        return str(self.args[0]) if self.args else self.violation.message

    def as_metadata(self) -> dict[str, Any]:
        metadata = self.violation.as_metadata()
        if self.run_id is not None:
            metadata["run_id"] = self.run_id
        return metadata


class AgentRunUsageStore(Protocol):
    """Persistence operations required to measure and stop a run."""

    def get_run(self, run_id: str) -> dict[str, Any] | None: ...

    def add_run_usage(
        self,
        run_id: str,
        *,
        tokens: int = 0,
        cost_usd: float = 0.0,
        tool_calls: int = 0,
    ) -> dict[str, Any]: ...

    def stop_run_for_limit(
        self, run_id: str, *, violation: dict[str, Any]
    ) -> dict[str, Any]: ...


def usage_from_run(run: dict[str, Any]) -> AgentUsage:
    """Build server-measured usage from a persisted run row.

    ``duration_ms`` is authoritative when the run has been closed; an open run
    measures elapsed time from ``started_at`` up to now so the duration limit is
    enforced even if the runtime never reports usage.
    """
    duration_ms = run.get("duration_ms")
    if duration_ms is not None:
        elapsed_seconds = float(duration_ms) / 1000.0
    else:
        elapsed_seconds = _elapsed_seconds(run.get("started_at"), run.get("finished_at"))
    return AgentUsage(
        tokens=int(run.get("total_tokens") or 0),
        cost_usd=float(run.get("total_cost_usd") or 0.0),
        tool_calls=int(run.get("total_tool_calls") or 0),
        elapsed_seconds=elapsed_seconds,
    )


class AgentLimitGuard:
    """Enforce a run's effective limits against server-measured usage."""

    def __init__(self, runs: AgentRunUsageStore) -> None:
        self._runs = runs

    def check(self, run_id: str, limits: AgentLimits) -> dict[str, Any]:
        """Stop the run and raise when its current usage already reached a limit."""
        run = self._require_run(run_id)
        self._raise_if_exceeded(run_id, limits, usage_from_run(run))
        return run

    def consume_tool_call(self, run_id: str, limits: AgentLimits) -> dict[str, Any]:
        """Allow one action start only while the run is still below every limit.

        The current usage is checked *before* counting the action, so a limit of
        ``N`` allows N actions and blocks the (N+1)-th start. The increment is
        performed by the store, which keeps the authoritative counter.
        """
        run = self._require_run(run_id)
        self._raise_if_exceeded(run_id, limits, usage_from_run(run))
        return self._runs.add_run_usage(run_id, tool_calls=1)

    def record_usage_and_check(
        self,
        run_id: str,
        limits: AgentLimits,
        *,
        tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> dict[str, Any]:
        """Add consumption and enforce the full effective limit set."""
        if tokens < 0 or cost_usd < 0:
            raise ValueError("usage")
        run = self._runs.add_run_usage(run_id, tokens=tokens, cost_usd=cost_usd)
        self._raise_if_exceeded(run_id, limits, usage_from_run(run))
        return run

    def _require_run(self, run_id: str) -> dict[str, Any]:
        run = self._runs.get_run(run_id)
        if run is None:
            raise LookupError(f"run not found: {run_id}")
        return run

    def _raise_if_exceeded(
        self, run_id: str, limits: AgentLimits, usage: AgentUsage
    ) -> None:
        violation = first_limit_violation(limits, usage)
        if violation is None:
            return
        logger.warning(
            "Agent limit reached: run=%s limit=%s observed=%s limit_value=%s",
            run_id,
            violation.field,
            violation.observed,
            violation.limit,
        )
        try:
            self._runs.stop_run_for_limit(
                run_id, violation={**violation.as_metadata(), "run_id": run_id}
            )
        except LookupError:
            logger.warning("Agent limit stop skipped: run %s no longer exists", run_id)
        raise AgentLimitError(violation, run_id=run_id)


def _elapsed_seconds(started_at: Any, finished_at: Any) -> float:
    start = _as_datetime(started_at)
    if start is None:
        return 0.0
    end = _as_datetime(finished_at) or datetime.now(timezone.utc)
    return max((end - start).total_seconds(), 0.0)


def _as_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)
    return None
