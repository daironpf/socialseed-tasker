"""Unit tests for the dedicated /agents/profiles router (issue #564).

Agent identities of the Users view live in ``users`` + ``agents_user`` with a
PostgreSQL-generated uid, no credential and no RBAC role. The router must be
registered before ``agent.py`` so ``/agents/profiles`` never falls into the
``/agents/{agent_id}`` path parameter.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from socialseed_tasker.auth.user_store import TOOLS_SEED, authenticate_user
from socialseed_tasker.infrastructure.web_api.routers import agent_profiles
from socialseed_tasker.infrastructure.web_api.schemas import (
    AgentProfileCreate,
    AgentProfileUpdate,
)
from tests.fakes.fake_pg_users import FakePgCursor, install_fake_pg

AGENT_BODY: dict = {
    "username": "bot-qa",
    "email": "bot@socialseed.com",
    "avatar": "🤖",
    "model": "gpt-4o",
    "specialization": "qa",
    "temperature": 0.2,
    "system_prompt": "You are a QA bot.",
    "tools": ["fs_read", "test_runner"],
    "write_access": ["issues"],
    "limits": {"max_tokens": 4000},
    "skills": ["Testing", "Pytest"],
    "enabled": True,
}


def _install_agent_env(monkeypatch: pytest.MonkeyPatch, cursor: FakePgCursor) -> None:
    """Run every /agents/profiles query against the stateful fake cursor."""
    install_fake_pg(monkeypatch, cursor)
    monkeypatch.setattr(agent_profiles, "get_database_url", lambda: "postgresql://fake")
    cursor.tools.update({slug: name for slug, name, _ in TOOLS_SEED})


def _create_agent() -> object:
    return agent_profiles.create_agent_profile(AgentProfileCreate(**AGENT_BODY))


# ---------------------------------------------------------------------------
# GET /agents/profiles (issue #564)
# ---------------------------------------------------------------------------


def test_list_agent_profiles_empty(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_agent_env(monkeypatch, cursor)

    response = agent_profiles.list_agent_profiles()

    assert response.data == []


def test_get_agent_profile_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_agent_env(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        agent_profiles.get_agent_profile("missing-uid")

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# POST /agents/profiles (issue #564)
# ---------------------------------------------------------------------------


def test_create_agent_profile_201_returns_uid(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_agent_env(monkeypatch, cursor)

    response = _create_agent()

    uid = response.data.id
    assert uid.startswith("pg-gen-"), uid
    assert cursor.users[uid]["user_type"] == "agent"
    agent = cursor.agents[uid]
    assert agent["email"] == "bot@socialseed.com"
    assert agent["model"] == "gpt-4o"
    assert agent["specialization"] == "qa"
    assert agent["temperature"] == 0.2
    assert agent["system_prompt"] == "You are a QA bot."
    assert agent["enabled"] is True
    assert response.data.type == "agent"
    assert response.data.role is None  # the front derives 'ai-agent' (#564)
    assert response.data.tools == ["fs_read", "test_runner"]
    assert response.data.write_access == ["issues"]
    assert response.data.limits == {"max_tokens": 4000}
    assert sorted(response.data.skills) == ["Pytest", "Testing"]
    assert cursor.user_skills[uid] == {"testing", "pytest"}


def test_create_agent_profile_unknown_tool_422(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_agent_env(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        agent_profiles.create_agent_profile(
            AgentProfileCreate(**{**AGENT_BODY, "tools": ["nope"]})
        )

    assert exc.value.status_code == 422
    assert "unknown tool: nope" in str(exc.value.detail)
    assert cursor.users == {}  # validated before anything is written


def test_create_agent_profile_duplicate_username_409(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_agent_env(monkeypatch, cursor)
    _create_agent()

    with pytest.raises(HTTPException) as exc:
        _create_agent()

    assert exc.value.status_code == 409
    assert len(cursor.users) == 1


# ---------------------------------------------------------------------------
# PUT /agents/profiles/{id} (issue #564)
# ---------------------------------------------------------------------------


def test_update_agent_profile(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_agent_env(monkeypatch, cursor)
    created = _create_agent()
    uid = created.data.id

    response = agent_profiles.update_agent_profile(
        uid,
        AgentProfileUpdate(
            username="bot-qa-2",
            model="claude-3",
            temperature=0.5,
            skills=["Refactor"],
            tools=["fs_read"],
            enabled=False,
        ),
    )

    assert response.data.username == "bot-qa-2"
    assert response.data.model == "claude-3"
    assert response.data.temperature == 0.5
    assert response.data.enabled is False
    assert response.data.tools == ["fs_read"]
    assert response.data.skills == ["Refactor"]
    # None keeps the stored values
    assert response.data.system_prompt == "You are a QA bot."
    assert response.data.email == "bot@socialseed.com"
    assert response.data.limits == {"max_tokens": 4000}
    assert cursor.users[uid]["username"] == "bot-qa-2"
    assert cursor.agents[uid]["model"] == "claude-3"
    assert cursor.user_skills[uid] == {"refactor"}

    with pytest.raises(HTTPException) as not_found:
        agent_profiles.update_agent_profile("missing-uid", AgentProfileUpdate(model="x"))
    assert not_found.value.status_code == 404

    _create_second = agent_profiles.create_agent_profile(
        AgentProfileCreate(**{**AGENT_BODY, "username": "bot-ci"})
    )
    with pytest.raises(HTTPException) as duplicate:
        agent_profiles.update_agent_profile(
            _create_second.data.id, AgentProfileUpdate(username="bot-qa-2")
        )
    assert duplicate.value.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /agents/profiles/{id} (issue #564)
# ---------------------------------------------------------------------------


def test_delete_agent_profile_removes_users_and_agents_user_rows(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_agent_env(monkeypatch, cursor)
    uid = _create_agent().data.id

    response = agent_profiles.delete_agent_profile(uid)

    assert response.data is True
    assert uid not in cursor.users
    assert uid not in cursor.agents
    assert uid not in cursor.user_skills

    with pytest.raises(HTTPException) as exc:
        agent_profiles.get_agent_profile(uid)
    assert exc.value.status_code == 404

    with pytest.raises(HTTPException) as again:
        agent_profiles.delete_agent_profile(uid)
    assert again.value.status_code == 404


def test_delete_agent_profile_never_touches_humans(monkeypatch: pytest.MonkeyPatch):
    """The user_type='agent' guard leaves human rows for DELETE /users (#562/#564)."""
    cursor = FakePgCursor()
    _install_agent_env(monkeypatch, cursor)
    cursor.users["human-1"] = {
        "id": "human-1",
        "username": "ana",
        "username_normalized": "ana",
        "user_type": "human",
        "created_at": None,
    }
    cursor.human["human-1"] = {"user_id": "human-1", "email": "ana@x.com", "role_id": "VIEWER"}

    with pytest.raises(HTTPException) as exc:
        agent_profiles.delete_agent_profile("human-1")

    assert exc.value.status_code == 404
    assert "human-1" in cursor.users
    assert "human-1" in cursor.human


# ---------------------------------------------------------------------------
# Routing and login isolation (issue #564)
# ---------------------------------------------------------------------------


def test_agent_profile_route_registered_before_agent_id():
    """/agents/profiles must win over /agents/{agent_id} in FastAPI's order."""
    from socialseed_tasker.infrastructure.web_api.app import create_app

    app = create_app()
    paths = [getattr(route, "path", "") for route in app.routes]
    profiles_index = paths.index("/api/v1/agents/profiles")
    agent_id_index = paths.index("/api/v1/agents/{agent_id}")
    assert profiles_index < agent_id_index


def test_agent_profile_no_login_with_missing_credential(monkeypatch: pytest.MonkeyPatch):
    """Agents have no human_user row nor password: they can never authenticate."""
    cursor = FakePgCursor()
    _install_agent_env(monkeypatch, cursor)
    _create_agent()

    assert authenticate_user("postgresql://fake", "bot-qa", "sesamo") is None


# ---------------------------------------------------------------------------
# 503 without TASKER_DATABASE_URL (issue #564)
# ---------------------------------------------------------------------------


def test_agent_profiles_503_without_database_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(agent_profiles, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        agent_profiles.list_agent_profiles()

    assert exc.value.status_code == 503
