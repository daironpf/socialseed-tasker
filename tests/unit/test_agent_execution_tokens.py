"""Tests for signed, run-scoped agent execution credentials."""

from __future__ import annotations

from socialseed_tasker.auth import tokens


def test_agent_execution_token_contains_only_its_run_scope():
    token = tokens.issue_agent_execution_token(
        agent_id="agent-1",
        run_id="run-1",
        issue_id="issue-1",
        project_id="project-1",
    )

    claims = tokens.verify_agent_execution_token(token)

    assert claims is not None
    assert claims["sub"] == "agent-1"
    assert claims["run_id"] == "run-1"
    assert claims["issue_id"] == "issue-1"
    assert claims["project_id"] == "project-1"
    assert claims["typ"] == "agent_execution"


def test_agent_execution_token_rejects_tampering_and_other_token_types():
    token = tokens.issue_agent_execution_token(
        agent_id="agent-1",
        run_id="run-1",
        issue_id="issue-1",
        project_id="project-1",
    )

    assert tokens.verify_agent_execution_token(token[:-1] + "x") is None
    assert tokens.verify_agent_execution_token("not-an-agent-token") is None
    assert tokens.verify_agent_execution_token(
        tokens.issue_tokens({"id": "user-1"})["access_token"]
    ) is None


def test_agent_execution_token_expires(monkeypatch):
    monkeypatch.setattr(tokens, "AGENT_EXECUTION_TTL", 1)
    monkeypatch.setattr(tokens.time, "time", lambda: 1_000)
    token = tokens.issue_agent_execution_token(
        agent_id="agent-1",
        run_id="run-1",
        issue_id="issue-1",
        project_id="project-1",
    )

    monkeypatch.setattr(tokens.time, "time", lambda: 1_002)

    assert tokens.verify_agent_execution_token(token) is None
