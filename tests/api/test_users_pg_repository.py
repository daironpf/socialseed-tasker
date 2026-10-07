"""Unit tests for PgUserRepository composed profiles (issue #558)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pytest

from socialseed_tasker.infrastructure.pg_user_repository import AGENT_ROLE_ALIAS, PgUserRepository
from tests.fakes.fake_pg_users import ScriptedCursor, install_fake_pg

NOW = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)
LAST_LOGIN = datetime(2026, 10, 6, 9, 30, tzinfo=timezone.utc)

# (id, username, user_type, created_at, h.email, h.role_id, h.avatar, h.github_handle,
#  h.preferences, h.is_active, a.email, a.avatar, a.model, a.specialization, a.enabled,
#  last_login, skills)
HUMAN_ROW: tuple[Any, ...] = (
    "uid-ana",
    "ana",
    "human",
    NOW,
    "ana@socialseed.com",
    "VIEWER",
    "🦊",
    "ana-gh",
    "dark",
    True,
    None,
    None,
    None,
    None,
    None,
    LAST_LOGIN,
    ["python", "vue"],
)
AGENT_ROW: tuple[Any, ...] = (
    "uid-bot",
    "bot-qa",
    "agent",
    NOW,
    None,
    None,
    None,
    None,
    None,
    None,
    "bot@socialseed.com",
    "🤖",
    "gpt-4o",
    "qa",
    True,
    None,
    ["testing"],
)


def _repo(monkeypatch: pytest.MonkeyPatch, cursor: ScriptedCursor) -> PgUserRepository:
    install_fake_pg(monkeypatch, cursor)
    return PgUserRepository("postgresql://fake")


def _head_sql(cursor: ScriptedCursor) -> str:
    return cursor.statements[-1][0]


class TestListUsers:
    def test_composes_human_and_agent_profiles_with_joins(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = ScriptedCursor(fetchall_rows=[HUMAN_ROW, AGENT_ROW])
        repo = _repo(monkeypatch, cursor)

        profiles = repo.list_users()

        sql = _head_sql(cursor)
        for fragment in (
            "LEFT JOIN human_user h ON h.user_id = u.id",
            "LEFT JOIN agents_user a ON a.user_id = u.id",
            "LEFT JOIN user_skills us ON us.user_id = u.id",
            "LEFT JOIN skills sk ON sk.id = us.skill_id",
            "MAX(s.created_at)",
            "s.event = 'login'",
            "GROUP BY u.id, h.user_id, a.user_id",
            "ORDER BY u.username",
            "LIMIT %s",
        ):
            assert fragment in sql
        assert cursor.last_params == (50,)

        human, agent = profiles
        assert human == {
            "id": "uid-ana",
            "username": "ana",
            "type": "human",
            "email": "ana@socialseed.com",
            "role": "VIEWER",
            "avatar": "🦊",
            "skills": ["python", "vue"],
            "model": None,
            "specialization": None,
            "is_active": True,
            "github_handle": "ana-gh",
            "preferences": "dark",
            "created_at": NOW,
            "last_login": LAST_LOGIN,
        }
        assert agent["role"] == AGENT_ROLE_ALIAS
        assert agent["type"] == "agent"
        assert agent["email"] == "bot@socialseed.com"
        assert agent["model"] == "gpt-4o"
        assert agent["specialization"] == "qa"
        assert agent["skills"] == ["testing"]
        assert agent["github_handle"] is None
        assert agent["preferences"] is None
        assert agent["is_active"] is True

    def test_role_filter_uses_derived_response_role(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = ScriptedCursor(fetchall_rows=[AGENT_ROW])
        repo = _repo(monkeypatch, cursor)

        profiles = repo.list_users(role=AGENT_ROLE_ALIAS, limit=10)

        sql = _head_sql(cursor)
        assert "THEN 'ai-agent' ELSE h.role_id" in sql
        assert "= %s" in sql
        assert cursor.last_params == (AGENT_ROLE_ALIAS, 10)
        assert [profile["id"] for profile in profiles] == ["uid-bot"]

    def test_empty_result_returns_empty_list(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = ScriptedCursor(fetchall_rows=[])
        repo = _repo(monkeypatch, cursor)

        assert repo.list_users() == []


class TestSingleLookups:
    def test_get_user_by_id(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = ScriptedCursor(fetchall_rows=[HUMAN_ROW])
        repo = _repo(monkeypatch, cursor)

        profile = repo.get_user("uid-ana")

        assert profile is not None and profile["id"] == "uid-ana"
        assert "WHERE u.id = %s" in _head_sql(cursor)
        assert cursor.last_params == ("uid-ana", 1)

    def test_get_user_returns_none_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = ScriptedCursor(fetchall_rows=[])
        repo = _repo(monkeypatch, cursor)

        assert repo.get_user("ghost") is None

    def test_get_user_by_email_queries_both_profiles(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = ScriptedCursor(fetchall_rows=[AGENT_ROW])
        repo = _repo(monkeypatch, cursor)

        profile = repo.get_user_by_email("bot@socialseed.com")

        assert profile is not None and profile["type"] == "agent"
        assert "h.email = %s OR a.email = %s" in _head_sql(cursor)
        assert cursor.last_params == ("bot@socialseed.com", "bot@socialseed.com", 1)

    def test_get_user_by_email_returns_none_when_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = ScriptedCursor(fetchall_rows=[])
        repo = _repo(monkeypatch, cursor)

        assert repo.get_user_by_email("ghost@socialseed.com") is None


class TestIdentityAndDelete:
    def test_list_identity_returns_username_uid_pairs(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = ScriptedCursor(fetchall_rows=[("admin", "admin"), ("bot-qa", "uid-bot")])
        repo = _repo(monkeypatch, cursor)

        assert repo.list_identity() == [("admin", "admin"), ("bot-qa", "uid-bot")]
        assert _head_sql(cursor) == "SELECT username, id FROM users ORDER BY username"

    def test_delete_user_row_reports_whether_row_was_removed(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = ScriptedCursor(rowcount=1)
        repo = _repo(monkeypatch, cursor)
        assert repo.delete_user_row("admin") is True
        assert _head_sql(cursor) == "DELETE FROM users WHERE id = %s"
        assert cursor.last_params == ("admin",)

        cursor.rowcount = 0
        assert repo.delete_user_row("ghost") is False


class TestRowMappingEdgeCases:
    def test_human_without_role_id_falls_back_to_developer(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        row = list(HUMAN_ROW)
        row[5] = None
        row[9] = None
        row[15] = None
        row[16] = []
        cursor = ScriptedCursor(fetchall_rows=[tuple(row)])
        repo = _repo(monkeypatch, cursor)

        profile = repo.get_user("uid-ana")

        assert profile is not None
        assert profile["role"] == "DEVELOPER"
        assert profile["is_active"] is True
        assert profile["skills"] == []

    def test_agent_without_enabled_flag_defaults_to_active(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        row = list(AGENT_ROW)
        row[14] = None
        cursor = ScriptedCursor(fetchall_rows=[tuple(row)])
        repo = _repo(monkeypatch, cursor)

        profile = repo.get_user("uid-bot")

        assert profile is not None
        assert profile["is_active"] is True
        assert profile["role"] == AGENT_ROLE_ALIAS
