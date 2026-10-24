"""Unit tests for the agent skills catalog endpoints (issue #577).

Agents have their own tables next to the human catalog: ``agent_skills``
(name + large behavior text) and ``agent_user_skills`` (assignments). These
endpoints feed the floating picker in the create/edit user modals. Issue #610
adds ``POST /agent-skills/import``: one uploaded ``.md`` becomes a catalog row.
"""

from __future__ import annotations

import asyncio
import io

import pytest
from fastapi import HTTPException, UploadFile

from socialseed_tasker.auth.user_store import (
    AGENT_SKILLS_SEED,
    PostgresAgentProfileStore,
    PostgresUserStore,
)
from socialseed_tasker.infrastructure.web_api.routers import agent_skills
from socialseed_tasker.infrastructure.web_api.schemas import (
    AgentSkillCreateRequest,
    AgentSkillUpdateRequest,
)
from tests.fakes.fake_pg_users import FakePgCursor, install_fake_pg


def _install(monkeypatch: pytest.MonkeyPatch, cursor: FakePgCursor) -> None:
    install_fake_pg(monkeypatch, cursor)
    monkeypatch.setattr(agent_skills, "get_database_url", lambda: "postgresql://fake")


# ---------------------------------------------------------------------------
# GET /agent-skills
# ---------------------------------------------------------------------------


def test_list_agent_skills_returns_name_and_behavior(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)

    created = agent_skills.create_agent_skill(
        AgentSkillCreateRequest(name="Code Reviewer", behavior="Review carefully.")
    )
    listing = agent_skills.list_agent_skills()

    assert created.data.id == "code-reviewer"
    assert created.data.behavior == "Review carefully."
    assert len(listing.data) == 1
    assert listing.data[0].name == "Code Reviewer"
    assert listing.data[0].behavior == "Review carefully."


def test_list_agent_skills_seeds_reach_the_catalog(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    store = PostgresUserStore("postgresql://fake")

    store.create_schema()
    seed_statements = [
        (sql, seq)
        for sql, seq in cursor.executemany_statements
        if "INSERT INTO agent_skills" in sql
    ]
    assert len(seed_statements) == 1
    sql, rows = seed_statements[0]
    assert "ON CONFLICT (id) DO NOTHING" in sql
    assert {(slug, name) for slug, name, _ in rows} == {
        (slug, name) for slug, name, _ in AGENT_SKILLS_SEED
    }
    # every seeded behavior is a large adoption text, never empty
    assert all(len(behavior) > 400 for _, _, behavior in rows)


# ---------------------------------------------------------------------------
# POST /agent-skills
# ---------------------------------------------------------------------------


def test_create_agent_skill_201_and_409_on_duplicate(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)

    created = agent_skills.create_agent_skill(
        AgentSkillCreateRequest(name="Security Analyst", behavior="Assume hostile input.")
    )
    assert created.data.id == "security-analyst"
    assert cursor.agent_skills["security-analyst"]["behavior"] == "Assume hostile input."

    with pytest.raises(HTTPException) as exc:
        agent_skills.create_agent_skill(
            AgentSkillCreateRequest(name="Security Analyst", behavior="x")
        )

    assert exc.value.status_code == 409


def test_create_agent_skill_422_on_empty_name(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        agent_skills.create_agent_skill(AgentSkillCreateRequest(name="   ", behavior="x"))

    assert exc.value.status_code == 422


# ---------------------------------------------------------------------------
# PUT /agent-skills/{id}
# ---------------------------------------------------------------------------


def test_update_agent_skill_rewrites_behavior_and_name(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    agent_skills.create_agent_skill(AgentSkillCreateRequest(name="QA Bot", behavior="v1"))

    updated = agent_skills.update_agent_skill(
        "qa-bot", AgentSkillUpdateRequest(name="QA Bot v2", behavior="v2")
    )

    assert updated.data.name == "QA Bot v2"
    assert updated.data.behavior == "v2"
    assert cursor.agent_skills["qa-bot"]["name"] == "QA Bot v2"


def test_update_agent_skill_404_and_409(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    agent_skills.create_agent_skill(AgentSkillCreateRequest(name="Alpha", behavior="a"))
    agent_skills.create_agent_skill(AgentSkillCreateRequest(name="Beta", behavior="b"))

    with pytest.raises(HTTPException) as not_found:
        agent_skills.update_agent_skill("ghost", AgentSkillUpdateRequest(behavior="x"))
    assert not_found.value.status_code == 404

    with pytest.raises(HTTPException) as conflict:
        agent_skills.update_agent_skill("alpha", AgentSkillUpdateRequest(name="Beta"))
    assert conflict.value.status_code == 409


def test_update_agent_skill_422_on_empty_name(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    agent_skills.create_agent_skill(AgentSkillCreateRequest(name="Alpha", behavior="a"))

    with pytest.raises(HTTPException) as exc:
        agent_skills.update_agent_skill("alpha", AgentSkillUpdateRequest(name="   "))

    assert exc.value.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /agent-skills/{id}
# ---------------------------------------------------------------------------


def test_delete_agent_skill_cascades_assignments(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    agent_skills.create_agent_skill(AgentSkillCreateRequest(name="Temp", behavior="t"))
    cursor.agent_user_skills["agent-1"] = {"temp"}

    response = agent_skills.delete_agent_skill("temp")

    assert response.data is True
    assert "temp" not in cursor.agent_skills
    assert "temp" not in cursor.agent_user_skills["agent-1"]

    with pytest.raises(HTTPException) as exc:
        agent_skills.delete_agent_skill("temp")

    assert exc.value.status_code == 404


# ---------------------------------------------------------------------------
# Migración del split (#577)
# ---------------------------------------------------------------------------


def test_create_schema_moves_agent_assignments_to_the_new_tables(
    monkeypatch: pytest.MonkeyPatch,
):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    # legacy state: both an agent and a human linked through user_skills
    cursor.users["agent-1"] = {
        "id": "agent-1",
        "username": "bot",
        "username_normalized": "bot",
        "user_type": "agent",
        "created_at": None,
    }
    cursor.users["u1"] = {
        "id": "u1",
        "username": "ana",
        "username_normalized": "ana",
        "user_type": "human",
        "created_at": None,
    }
    cursor.skills["python"] = "Python"
    cursor.skills["vue"] = "Vue"
    cursor.user_skills = {"agent-1": {"python"}, "u1": {"vue", "python"}}
    store = PostgresUserStore("postgresql://fake")

    store.create_schema()
    store.create_schema()  # idempotent

    assert cursor.user_skills == {"u1": {"vue", "python"}}  # agent links dropped
    assert cursor.agent_user_skills["agent-1"] == {"python"}
    assert cursor.agent_skills["python"]["name"] == "Python"
    assert cursor.agent_skills["python"]["behavior"] == ""  # filled in later via PUT
    assert "vue" not in cursor.agent_user_skills.get("agent-1", set())


def test_profile_skills_read_from_agent_tables(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    store = PostgresAgentProfileStore("postgresql://fake")
    cursor.users["agent-1"] = {
        "id": "agent-1",
        "username": "bot",
        "username_normalized": "bot",
        "user_type": "agent",
        "created_at": None,
    }
    cursor.agents["agent-1"] = {"email": None, "enabled": True}
    cursor.agent_skills["reviewer"] = {"name": "Reviewer", "behavior": "b"}
    cursor.agent_user_skills["agent-1"] = {"reviewer"}
    cursor.skills["python"] = "Python"  # human catalog must NOT leak
    cursor.user_skills["agent-1"] = {"python"}  # stale row ignored after migration

    profile = store.get_profile("agent-1")

    assert profile is not None
    assert profile["skills"] == ["Reviewer"]


def test_assigning_a_renamed_skill_links_the_stable_id(monkeypatch: pytest.MonkeyPatch):
    """Rename keeps the id (#577 PUT); assignment by the NEW name must link it (#610)."""
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    agent_skills.create_agent_skill(AgentSkillCreateRequest(name="QA Bot", behavior="v1"))
    agent_skills.update_agent_skill("qa-bot", AgentSkillUpdateRequest(name="QA Bot Renamed"))

    store = PostgresAgentProfileStore("postgresql://fake")
    uid = store.create_profile(username="renamed-probe", skills=["QA Bot Renamed"])

    # links the STABLE id, not a fresh slug of the new name
    assert cursor.agent_user_skills[uid] == {"qa-bot"}
    assert "qa-bot-renamed" not in cursor.agent_skills
    # the skill keeps its rewritten behavior (not reset to '')
    assert cursor.agent_skills["qa-bot"]["behavior"] == "v1"
    profile = store.get_profile(uid)
    assert profile is not None
    assert profile["skills"] == ["QA Bot Renamed"]


# ---------------------------------------------------------------------------
# 503 sin database
# ---------------------------------------------------------------------------


def test_agent_skills_503_without_database_url(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    monkeypatch.setattr(agent_skills, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        agent_skills.list_agent_skills()

    assert exc.value.status_code == 503


# ---------------------------------------------------------------------------
# POST /agent-skills/import (#610)
# ---------------------------------------------------------------------------


def _upload(content: bytes, filename: str = "skill.md") -> UploadFile:
    return UploadFile(filename=filename, file=io.BytesIO(content))


def test_import_agent_skill_from_heading_and_full_text(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    markdown = "# Code Reviewer\n\nCheck every diff twice.\n"

    created = asyncio.run(agent_skills.import_agent_skill(_upload(markdown.encode("utf-8"))))

    assert created.data.id == "code-reviewer"
    assert created.data.name == "Code Reviewer"
    assert created.data.behavior == "# Code Reviewer\n\nCheck every diff twice."


def test_import_agent_skill_falls_back_to_filename_stem(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    markdown = "No heading here, just adoption rules."

    created = asyncio.run(
        agent_skills.import_agent_skill(
            _upload(markdown.encode("utf-8"), filename="Data_Quality Bot.md")
        )
    )

    assert created.data.name == "Data Quality Bot"
    assert created.data.id == "data-quality-bot"
    assert created.data.behavior == markdown


def test_import_agent_skill_422_on_bad_extension_empty_and_undecodable(
    monkeypatch: pytest.MonkeyPatch,
):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)

    with pytest.raises(HTTPException) as bad_ext:
        asyncio.run(agent_skills.import_agent_skill(_upload(b"x", filename="skill.txt")))
    assert bad_ext.value.status_code == 422

    with pytest.raises(HTTPException) as empty:
        asyncio.run(agent_skills.import_agent_skill(_upload(b"   \n")))
    assert empty.value.status_code == 422

    with pytest.raises(HTTPException) as undecodable:
        asyncio.run(agent_skills.import_agent_skill(_upload(b"\xff\xfe\x00bad", filename="x.md")))
    assert undecodable.value.status_code == 422

    with pytest.raises(HTTPException) as no_name:
        asyncio.run(agent_skills.import_agent_skill(_upload(b"#    \nbody", filename="skill.md")))
    assert no_name.value.status_code == 422


def test_import_agent_skill_409_on_duplicate(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)

    asyncio.run(agent_skills.import_agent_skill(_upload(b"# QA Bot\nrules")))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(agent_skills.import_agent_skill(_upload(b"# QA Bot\nother rules")))

    assert exc.value.status_code == 409
    assert cursor.agent_skills["qa-bot"]["behavior"] == "# QA Bot\nrules"
