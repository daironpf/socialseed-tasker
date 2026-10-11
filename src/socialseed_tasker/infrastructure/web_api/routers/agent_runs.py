"""API router for persistent agent run history (issue #574).

Greenfield tables ``agent_runs`` + ``agent_run_logs`` give the Studio a
history of agent executions that survives API restarts. The in-memory SSE
streaming of ``realtime.py`` (#517/#472) is untouched: it flushes each
posted log best-effort into the open run via :func:`append_agent_log_best_effort`
and the run lifecycle is closed from ``/issues/{id}/agent/finish``.

Registered in ``app.py`` after ``agent.py``; the ``/agents/{agent_id}/runs``
template never collides with ``/agents/{agent_id}`` or its suffixes because
each extra path segment is a distinct literal.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from socialseed_tasker.auth.user_store import PostgresAgentProfileStore
from socialseed_tasker.config.storage import get_database_url
from socialseed_tasker.infrastructure.web_api.schemas import (
    AgentRunCreate,
    AgentRunLogCreate,
    AgentRunLogResponse,
    AgentRunResponse,
    AgentRunUpdate,
    APIResponse,
    Meta,
)

logger = logging.getLogger(__name__)

agent_runs_router = APIRouter()


def _pg_store() -> PostgresAgentProfileStore:
    """PostgreSQL store for /agents/{id}/runs (issue #574)."""
    database_url = get_database_url()
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL not configured: TASKER_DATABASE_URL is not set",
        )
    return PostgresAgentProfileStore(database_url)


def _run_to_response(run: dict[str, Any]) -> AgentRunResponse:
    return AgentRunResponse(
        id=str(run["id"]),
        agent_id=str(run["agent_id"]),
        issue_id=run.get("issue_id"),
        status=run["status"],
        model=run.get("model"),
        started_at=run.get("started_at"),
        finished_at=run.get("finished_at"),
        total_tokens=run.get("total_tokens"),
        total_tool_calls=run.get("total_tool_calls"),
        duration_ms=run.get("duration_ms"),
        summary=run.get("summary"),
    )


def _log_to_response(entry: dict[str, Any]) -> AgentRunLogResponse:
    return AgentRunLogResponse(
        run_id=str(entry["run_id"]),
        seq=int(entry["seq"]),
        timestamp=entry.get("timestamp"),
        type=entry["type"],
        content_markdown=entry.get("content_markdown"),
        metadata=entry.get("metadata"),
    )


# ---------------------------------------------------------------------------
# Best-effort lifecycle helpers used by realtime.py / issues.py (issue #574).
# ---------------------------------------------------------------------------


def open_run_best_effort(agent_id: str, *, issue_id: str | None = None, model: str | None = None) -> str | None:
    """Open (or reuse) a ``running`` run without breaking the caller.

    Returns the run id, or ``None`` when PostgreSQL is not configured, the
    agent is unknown, or any error occurs; failures are logged as warnings.
    """
    database_url = get_database_url()
    if not database_url:
        return None
    try:
        return PostgresAgentProfileStore(database_url).ensure_running_run(agent_id, issue_id=issue_id, model=model)
    except Exception as exc:  # noqa: BLE001 - best-effort persistence
        logger.warning("agent run open skipped for %s: %s", agent_id, exc)
        return None


def close_run_best_effort(
    agent_id: str,
    *,
    issue_id: str | None = None,
    status: str = "completed",
    summary: str | None = None,
) -> bool:
    """Close the agent's open run without breaking the caller (see above)."""
    database_url = get_database_url()
    if not database_url:
        return False
    try:
        return PostgresAgentProfileStore(database_url).close_open_run(
            agent_id, issue_id=issue_id, status=status, summary=summary
        )
    except Exception as exc:  # noqa: BLE001 - best-effort persistence
        logger.warning("agent run close skipped for %s: %s", agent_id, exc)
        return False


_PERSISTED_LOG_TYPES = {"reasoning", "progress", "files", "debt", "tool_call", "error", "violation"}


def append_agent_log_best_effort(issue_id: str, payload: dict[str, Any]) -> None:
    """Flush one realtime SSE log entry into the agent's open run (issue #574).

    The ``agent_id`` is taken from the posted payload; entries without one
    (the common case for legacy emitters) stay SSE-only and are skipped.
    """
    agent_id = payload.get("agent_id")
    if not agent_id or not isinstance(agent_id, str):
        return
    database_url = get_database_url()
    if not database_url:
        return
    try:
        store = PostgresAgentProfileStore(database_url)
        run_id = store.ensure_running_run(agent_id, issue_id=issue_id)
        if not run_id:
            return
        log_type = str(payload.get("type") or "progress")
        if log_type not in _PERSISTED_LOG_TYPES:
            log_type = "progress"
        store.append_run_log(
            run_id,
            type=log_type,
            content_markdown=payload.get("content_markdown"),
            metadata=payload.get("metadata"),
        )
    except Exception as exc:  # noqa: BLE001 - best-effort persistence
        logger.warning("agent run log flush skipped for issue %s: %s", issue_id, exc)


# ---------------------------------------------------------------------------
# Endpoints.
# ---------------------------------------------------------------------------


@agent_runs_router.post(
    "/agents/{agent_id}/runs",
    response_model=APIResponse[AgentRunResponse],
    status_code=201,
    summary="Open agent run",
    description="Create a ``running`` run for an agent (issue #574).",
)
def create_agent_run(agent_id: str, body: AgentRunCreate) -> APIResponse[AgentRunResponse]:
    """Open a run; 404 when the agent uid is not a PG agent user."""
    try:
        run = _pg_store().create_run(agent_id, issue_id=body.issue_id, model=body.model)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Agent not found") from exc
    return APIResponse(data=_run_to_response(run), meta=Meta(request_id=None))


@agent_runs_router.get(
    "/agents/{agent_id}/runs",
    response_model=APIResponse[list[AgentRunResponse]],
    summary="List agent runs",
    description="List an agent's runs newest-first (issue #574).",
)
def list_agent_runs(
    agent_id: str,
    limit: int = Query(50, ge=1, le=200),
) -> APIResponse[list[AgentRunResponse]]:
    """List an agent's runs; 404 when the agent uid is unknown."""
    try:
        runs = _pg_store().list_runs(agent_id, limit=limit)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Agent not found") from exc
    return APIResponse(data=[_run_to_response(run) for run in runs], meta=Meta(request_id=None))


@agent_runs_router.post(
    "/runs/{run_id}/logs",
    response_model=APIResponse[AgentRunLogResponse],
    status_code=201,
    summary="Append run log",
    description="Append one log entry to a run; seq is assigned by the store (issue #574).",
)
def append_agent_run_log(run_id: str, body: AgentRunLogCreate) -> APIResponse[AgentRunLogResponse]:
    """Append a log entry; 404 when the run is unknown."""
    try:
        entry = _pg_store().append_run_log(
            run_id,
            type=body.type,
            content_markdown=body.content_markdown,
            metadata=body.metadata,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    return APIResponse(data=_log_to_response(entry), meta=Meta(request_id=None))


@agent_runs_router.get(
    "/runs/{run_id}/logs",
    response_model=APIResponse[list[AgentRunLogResponse]],
    summary="List run logs",
    description="List a run's log entries ordered by seq (issue #574).",
)
def list_agent_run_logs(run_id: str) -> APIResponse[list[AgentRunLogResponse]]:
    """List a run's logs; 404 when the run is unknown."""
    try:
        entries = _pg_store().list_run_logs(run_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    return APIResponse(data=[_log_to_response(entry) for entry in entries], meta=Meta(request_id=None))


@agent_runs_router.patch(
    "/runs/{run_id}",
    response_model=APIResponse[AgentRunResponse],
    summary="Update agent run",
    description="Partially update a run (status/tokens/summary...); None keeps the stored value (issue #574).",
)
def update_agent_run(run_id: str, body: AgentRunUpdate) -> APIResponse[AgentRunResponse]:
    """Partial run update; 404 when the run is unknown, 422 on bad status (schema Literal)."""
    try:
        run = _pg_store().update_run(
            run_id,
            status=body.status,
            finished_at=body.finished_at,
            total_tokens=body.total_tokens,
            total_tool_calls=body.total_tool_calls,
            duration_ms=body.duration_ms,
            summary=body.summary,
            model=body.model,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Run not found") from exc
    return APIResponse(data=_run_to_response(run), meta=Meta(request_id=None))


@agent_runs_router.delete(
    "/runs/{run_id}",
    summary="Delete agent run",
    description="Delete a run; logs cascade (issue #574).",
)
def delete_agent_run(run_id: str) -> APIResponse[bool]:
    """Delete a run; 404 when the run is unknown."""
    deleted = _pg_store().delete_run(run_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Run not found")
    return APIResponse(data=True, meta=Meta(request_id=None))
