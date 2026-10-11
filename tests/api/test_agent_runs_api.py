"""Unit tests for the persistent agent run history router (issue #574).

``agent_runs`` + ``agent_run_logs`` give the Studio a restart-proof history
of agent executions. The SSE streaming of realtime.py stays in memory; the
best-effort flush helpers are covered here too.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from socialseed_tasker.infrastructure.web_api.routers import agent_runs
from socialseed_tasker.infrastructure.web_api.schemas import (
    AgentRunCreate,
    AgentRunLogCreate,
    AgentRunUpdate,
)
from tests.fakes.fake_pg_users import FakePgCursor, install_fake_pg

AGENT_ID = "builder-1"


def _install_runs_env(monkeypatch: pytest.MonkeyPatch, cursor: FakePgCursor) -> None:
    install_fake_pg(monkeypatch, cursor)
    monkeypatch.setattr(agent_runs, "get_database_url", lambda: "postgresql://fake")


def _seed_agent(cursor: FakePgCursor, uid: str = AGENT_ID) -> None:
    cursor.users[uid] = {
        "id": uid,
        "username": "builder",
        "username_normalized": "builder",
        "user_type": "agent",
        "created_at": None,
    }


def _open_run() -> object:
    return agent_runs.create_agent_run(AGENT_ID, AgentRunCreate(issue_id="ISSUE-1", model="gpt-4o"))


# ---------------------------------------------------------------------------
# POST /agents/{id}/runs + GET /agents/{id}/runs (issue #574)
# ---------------------------------------------------------------------------


def test_open_run_201_and_list_runs(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)
    _seed_agent(cursor)

    created = _open_run()

    assert created.data.status == "running"
    assert created.data.agent_id == AGENT_ID
    assert created.data.issue_id == "ISSUE-1"
    assert created.data.model == "gpt-4o"
    assert created.data.started_at is not None
    listed = agent_runs.list_agent_runs(AGENT_ID, limit=50)
    assert [run.id for run in listed.data] == [created.data.id]
    assert listed.data[0].status == "running"


def test_open_run_unknown_agent_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        agent_runs.create_agent_run("ghost", AgentRunCreate())

    assert exc.value.status_code == 404
    assert cursor.runs == {}


def test_list_runs_unknown_agent_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        agent_runs.list_agent_runs("ghost")

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# POST/GET /runs/{id}/logs (issue #574)
# ---------------------------------------------------------------------------


def test_append_log_201_assigns_seq_and_lists_ordered(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)
    _seed_agent(cursor)
    run_id = _open_run().data.id

    first = agent_runs.append_agent_run_log(run_id, AgentRunLogCreate(type="reasoning", content_markdown="pensando"))
    second = agent_runs.append_agent_run_log(
        run_id, AgentRunLogCreate(type="progress", content_markdown="avanzo", metadata={"step": 1})
    )

    assert first.data.seq == 1
    assert second.data.seq == 2
    logs = agent_runs.list_agent_run_logs(run_id)
    assert [entry.seq for entry in logs.data] == [1, 2]
    assert logs.data[0].type == "reasoning"
    assert logs.data[1].metadata == {"step": 1}


def test_append_log_unknown_run_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        agent_runs.append_agent_run_log("ghost-run", AgentRunLogCreate(content_markdown="x"))

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# PATCH /runs/{id} (issue #574)
# ---------------------------------------------------------------------------


def test_update_run_partial_persists(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)
    _seed_agent(cursor)
    run_id = _open_run().data.id

    closed = agent_runs.update_agent_run(
        run_id,
        AgentRunUpdate(
            status="completed",
            total_tokens=1200,
            finished_at=datetime(2026, 10, 11, 9, 0, tzinfo=timezone.utc),
        ),
    )

    assert closed.data.status == "completed"
    assert closed.data.total_tokens == 1200
    assert closed.data.finished_at is not None
    second = agent_runs.update_agent_run(run_id, AgentRunUpdate(summary="resumen final"))
    assert second.data.status == "completed"  # None keeps the stored value
    assert second.data.total_tokens == 1200
    assert second.data.finished_at == datetime(2026, 10, 11, 9, 0, tzinfo=timezone.utc)
    assert second.data.summary == "resumen final"


def test_update_run_status_validation_422(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)

    with pytest.raises(ValidationError):
        AgentRunUpdate(status="nope")


def test_update_run_unknown_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        agent_runs.update_agent_run("ghost-run", AgentRunUpdate(status="failed"))

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /runs/{id} (issue #574)
# ---------------------------------------------------------------------------


def test_delete_run_200_cascades_logs(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)
    _seed_agent(cursor)
    run_id = _open_run().data.id
    agent_runs.append_agent_run_log(run_id, AgentRunLogCreate(content_markdown="hola"))

    deleted = agent_runs.delete_agent_run(run_id)

    assert deleted.data is True
    assert run_id not in cursor.runs
    assert cursor.run_logs.get(run_id, []) == []
    with pytest.raises(HTTPException) as exc:
        agent_runs.list_agent_run_logs(run_id)
    assert exc.value.status_code == 404


def test_delete_run_unknown_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        agent_runs.delete_agent_run("ghost-run")

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# 503 sin PostgreSQL (patrón #564/#572)
# ---------------------------------------------------------------------------


def test_agent_runs_503_without_database_url(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)
    monkeypatch.setattr(agent_runs, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        agent_runs.create_agent_run(AGENT_ID, AgentRunCreate())

    assert exc.value.status_code == 503


# ---------------------------------------------------------------------------
# Best-effort flush de realtime.py (issue #574)
# ---------------------------------------------------------------------------


def test_append_agent_log_best_effort_persists_with_agent_id(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)
    _seed_agent(cursor)

    agent_runs.append_agent_log_best_effort(
        "ISSUE-1",
        {"agent_id": AGENT_ID, "type": "reasoning", "content_markdown": "pensando", "metadata": {"n": 1}},
    )

    runs = [run for run in cursor.runs.values() if run["agent_id"] == AGENT_ID]
    assert len(runs) == 1
    assert runs[0]["status"] == "running"
    logs = cursor.run_logs[runs[0]["id"]]
    assert logs[0]["type"] == "reasoning"
    assert logs[0]["content_markdown"] == "pensando"


def test_append_agent_log_best_effort_skips_without_agent_id(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)

    agent_runs.append_agent_log_best_effort("ISSUE-1", {"type": "progress", "content_markdown": "x"})

    assert cursor.runs == {}


def test_open_and_close_run_best_effort_lifecycle(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)
    _seed_agent(cursor)

    run_id = agent_runs.open_run_best_effort(AGENT_ID, issue_id="ISSUE-1")
    assert run_id is not None
    again = agent_runs.open_run_best_effort(AGENT_ID, issue_id="ISSUE-1")
    assert again == run_id  # reuses the open run
    assert agent_runs.close_run_best_effort(AGENT_ID, issue_id="ISSUE-1", status="completed") is True
    assert cursor.runs[run_id]["status"] == "completed"
    assert cursor.runs[run_id]["duration_ms"] == 300000
    assert agent_runs.close_run_best_effort("ghost", issue_id="ISSUE-1") is False


def test_open_run_best_effort_unknown_agent_returns_none(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)

    assert agent_runs.open_run_best_effort("ghost", issue_id="ISSUE-1") is None
    assert cursor.runs == {}


def test_agent_log_stream_persists_best_effort_never_raises(monkeypatch: pytest.MonkeyPatch):
    """A broken PostgreSQL never breaks the SSE POST (#574: flush is best-effort)."""

    class _ExplodingStore:
        def __init__(self, _database_url: str) -> None:
            raise RuntimeError("postgres down")

    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)
    monkeypatch.setattr(agent_runs, "PostgresAgentProfileStore", _ExplodingStore)

    agent_runs.append_agent_log_best_effort(
        "ISSUE-1",
        {"agent_id": AGENT_ID, "type": "progress", "content_markdown": "x"},
    )  # must not raise

    assert cursor.runs == {}


def test_delete_agent_cascades_runs_and_logs(monkeypatch: pytest.MonkeyPatch):
    """DELETE /agents/profiles removes the agent's runs through ON DELETE CASCADE (#574)."""
    cursor = FakePgCursor()
    _install_runs_env(monkeypatch, cursor)
    _seed_agent(cursor)
    run_id = _open_run().data.id
    agent_runs.append_agent_run_log(run_id, AgentRunLogCreate(content_markdown="hola"))

    from socialseed_tasker.auth.user_store import PostgresAgentProfileStore

    assert PostgresAgentProfileStore("postgresql://fake").delete_profile(AGENT_ID) is True

    assert run_id not in cursor.runs
    assert cursor.run_logs.get(run_id, []) == []
