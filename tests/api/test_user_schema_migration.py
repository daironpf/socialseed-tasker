"""Schema creation, legacy migration and credential tests for issue #558."""

from __future__ import annotations

from typing import Any

import pytest

from socialseed_tasker.auth import user_store as user_store_module
from socialseed_tasker.auth.user_store import (
    PostgresUserStore,
    authenticate_user,
    hash_password,
    map_role,
    normalize_user_type,
    skill_slug,
)
from tests.fakes.fake_pg_users import FakePgCursor, install_fake_pg

EXPECTED_TABLES = {
    "roles",
    "skills",
    "tools",
    "users",
    "human_user",
    "agents_user",
    "user_skills",
    "session_logs",
}

HUMAN_LEGACY_ROW = (
    "u1",
    "Pedro Pérez",
    "pedro.perez",
    "pedro@socialseed.com",
    "$2b$12$legacyhash",
    "lead-developer",
    "human",
    "2026-01-15T10:00:00+00:00",
)
AGENT_LEGACY_ROW = (
    "u2",
    "Bot Dev",
    "botdev",
    "bot@socialseed.com",
    "",
    "developer",
    "agent",
    "2026-01-16T10:00:00+00:00",
)
ADMIN_LEGACY_ROW = (
    "u3",
    "Root",
    "root",
    "root@socialseed.com",
    "$2b$12$adminhash",
    "ADMIN",
    None,
    None,
)


def _store(monkeypatch: pytest.MonkeyPatch, cursor: FakePgCursor) -> PostgresUserStore:
    install_fake_pg(monkeypatch, cursor)
    return PostgresUserStore("postgresql://fake")


def _legacy_schema(cursor: FakePgCursor, *, with_last_login: bool = False) -> None:
    cursor.tables.add("users")
    cursor.columns["users"] = {
        "id",
        "username",
        "username_normalized",
        "email",
        "password_hash",
        "role",
        "type",
        "created_at",
    }
    if with_last_login:
        cursor.columns["users"].add("last_login")


class TestHelpers:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("agent", "agent"), ("AGENT", "agent"), ("human", "human"), ("admin", "human"), (None, "human")],
    )
    def test_normalize_user_type(self, raw: str | None, expected: str) -> None:
        assert normalize_user_type(raw) == expected

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("ADMIN", "ADMIN"),
            ("admin", "ADMIN"),
            ("lead-developer", "DEVELOPER"),
            (None, "DEVELOPER"),
            ("x", "DEVELOPER"),
        ],
    )
    def test_map_role(self, raw: str | None, expected: str) -> None:
        assert map_role(raw) == expected

    @pytest.mark.parametrize(("raw", "expected"), [("Vue", "vue"), ("CI/CD", "ci-cd"), ("  Go  ", "go")])
    def test_skill_slug(self, raw: str, expected: str) -> None:
        assert skill_slug(raw) == expected


class TestCreateSchema:
    def test_fresh_database_creates_normalized_tables_and_seeds(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)

        store.create_schema()

        assert cursor.tables >= EXPECTED_TABLES
        assert "user_type" in cursor.columns["users"]
        assert "role_id" in cursor.columns["human_user"]
        assert "model" in cursor.columns["agents_user"]
        assert "event" in cursor.columns["session_logs"]

        role_seeds = [seq for sql, seq in cursor.executemany_statements if "INSERT INTO roles" in sql]
        assert role_seeds and {row[0] for row in role_seeds[0]} == {"ADMIN", "DEVELOPER", "VIEWER"}
        tool_seeds = [seq for sql, seq in cursor.executemany_statements if "INSERT INTO tools" in sql]
        assert tool_seeds and len(tool_seeds[0]) >= 9
        tool_ids = {row[0] for row in tool_seeds[0]}
        assert {"code_search", "web_search", "test_runner", "git_tools"} <= tool_ids

        joined = "\n".join(cursor.sql_log)
        assert "ALTER TABLE" not in joined
        assert "ix_users_user_type" in joined
        assert "ix_session_logs_user_created" in joined

    def test_second_run_on_normalized_database_is_idempotent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)

        store.create_schema()
        store.create_schema()

        assert cursor.tables >= EXPECTED_TABLES
        assert "ALTER TABLE" not in "\n".join(cursor.sql_log)
        role_seeds = [seq for sql, seq in cursor.executemany_statements if "INSERT INTO roles" in sql]
        assert len(role_seeds) == 2
        assert all("ON CONFLICT" in sql for sql, _ in cursor.executemany_statements)


class TestLegacyMigration:
    def test_migrates_legacy_rows_preserving_ids_and_mapping_roles(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = FakePgCursor()
        _legacy_schema(cursor)
        cursor.legacy_rows = [HUMAN_LEGACY_ROW, AGENT_LEGACY_ROW, ADMIN_LEGACY_ROW]
        store = _store(monkeypatch, cursor)

        store.create_schema()

        assert "users_legacy" in cursor.tables
        assert 'ALTER TABLE users RENAME TO "users_legacy"' in cursor.sql_log
        assert set(cursor.users) == {"u1", "u2", "u3"}
        assert cursor.users["u1"]["user_type"] == "human"
        assert cursor.users["u2"]["user_type"] == "agent"
        assert cursor.users["u3"]["user_type"] == "human"
        assert cursor.human["u1"]["role_id"] == "DEVELOPER"
        assert cursor.human["u3"]["role_id"] == "ADMIN"
        assert cursor.human["u1"]["password_hash"] == "$2b$12$legacyhash"
        assert "u2" in cursor.agents and "u2" not in cursor.human

    def test_migration_with_last_login_column_adds_synthetic_session_log(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = FakePgCursor()
        _legacy_schema(cursor, with_last_login=True)
        cursor.legacy_rows = [
            HUMAN_LEGACY_ROW + ("2026-02-01T09:00:00+00:00",),
            AGENT_LEGACY_ROW + (None,),
        ]
        store = _store(monkeypatch, cursor)

        store.create_schema()

        assert len(cursor.session_logs) == 1
        assert cursor.session_logs[0][0] == "u1"
        assert cursor.session_logs[0][1] == "login"

    def test_migration_is_idempotent_on_second_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = FakePgCursor()
        _legacy_schema(cursor, with_last_login=True)
        cursor.legacy_rows = [HUMAN_LEGACY_ROW + ("2026-02-01T09:00:00+00:00",)]
        store = _store(monkeypatch, cursor)

        store.create_schema()
        users_after_first = dict(cursor.users)
        logs_after_first = list(cursor.session_logs)

        store.create_schema()

        assert cursor.users == users_after_first
        assert cursor.session_logs == logs_after_first
        migration_inserts = [sql for sql in cursor.sql_log if sql.startswith("INSERT INTO users")]
        assert migration_inserts and all("ON CONFLICT DO NOTHING" in sql for sql in migration_inserts)

    def test_resume_after_rename_without_users_table(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = FakePgCursor()
        cursor.tables.add("users_legacy")
        cursor.columns["users_legacy"] = {
            "id",
            "username",
            "username_normalized",
            "email",
            "password_hash",
            "role",
            "type",
            "created_at",
        }
        cursor.legacy_rows = [HUMAN_LEGACY_ROW]
        store = _store(monkeypatch, cursor)

        store.create_schema()

        assert "u1" in cursor.users
        assert "users" in cursor.tables

    def test_verify_counts_raises_when_identity_row_is_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = FakePgCursor()
        _legacy_schema(cursor)
        cursor.legacy_rows = [HUMAN_LEGACY_ROW]
        store = _store(monkeypatch, cursor)

        with pytest.raises(RuntimeError, match="migration incomplete"):
            store._verify_migration(cursor, "users_legacy")

    def test_verify_counts_raises_when_profile_row_is_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = FakePgCursor()
        _legacy_schema(cursor)
        cursor.legacy_rows = [HUMAN_LEGACY_ROW]
        cursor.users["u1"] = {
            "id": "u1",
            "username": "Pedro Pérez",
            "username_normalized": "pedro.perez",
            "user_type": "human",
            "created_at": None,
        }
        store = _store(monkeypatch, cursor)

        with pytest.raises(RuntimeError, match="migration incomplete"):
            store._verify_migration(cursor, "users_legacy")


class TestUpsertUser:
    def test_human_insert_writes_identity_and_profile_rows(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)
        store.create_schema()

        status = store.upsert_user(
            user_id="admin",
            username="admin",
            username_normalized="admin",
            email="admin@socialseed.com",
            password_hash=hash_password("admin"),
            role="admin",
            user_type="admin",
            created_at="2026-10-07T00:00:00+00:00",
        )

        assert status == "created"
        assert cursor.users["admin"]["user_type"] == "human"
        assert cursor.human["admin"]["role_id"] == "ADMIN"
        assert cursor.human["admin"]["email"] == "admin@socialseed.com"
        assert "admin" not in cursor.agents

    def test_agent_insert_writes_agents_profile_row(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)
        store.create_schema()

        status = store.upsert_user(
            user_id="bot",
            username="bot",
            username_normalized="bot",
            email="bot@socialseed.com",
            password_hash="",
            role=None,
            user_type="agent",
            created_at=None,
        )

        assert status == "created"
        assert cursor.users["bot"]["user_type"] == "agent"
        assert "bot" in cursor.agents and "bot" not in cursor.human

    def test_second_upsert_returns_existing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)
        store.create_schema()
        kwargs: dict[str, Any] = dict(
            user_id="u1",
            username="pedro",
            username_normalized="pedro",
            email="pedro@socialseed.com",
            password_hash=hash_password("pedro"),
            role="developer",
            user_type="human",
            created_at=None,
        )
        assert store.upsert_user(**kwargs) == "created"
        assert store.upsert_user(**kwargs) == "existing"

    def test_missing_uid_generates_id_via_returning(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)
        store.create_schema()

        status = store.upsert_user(
            user_id=None,
            username="Nuevo",
            username_normalized="nuevo",
            email=None,
            password_hash=hash_password("nuevo"),
            role="viewer",
            user_type="human",
            created_at=None,
        )

        assert status == "created"
        insert_sql = next(sql for sql in cursor.sql_log if sql.startswith("INSERT INTO users"))
        assert "INSERT INTO users (username, username_normalized, user_type, created_at)" in insert_sql
        assert "RETURNING id" in insert_sql
        assert cursor.users and next(iter(cursor.users)) == "pg-gen-1"
        assert cursor.human["pg-gen-1"]["role_id"] == "VIEWER"


class TestUpsertProfile:
    def test_merges_avatar_skills_and_model(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)
        store.create_schema()
        store.upsert_user(
            user_id="u1",
            username="pedro",
            username_normalized="pedro",
            email=None,
            password_hash="x",
            role="developer",
            user_type="human",
            created_at=None,
        )
        store.upsert_user(
            user_id="bot",
            username="bot",
            username_normalized="bot",
            email=None,
            password_hash="",
            role=None,
            user_type="agent",
            created_at=None,
        )

        store.upsert_profile(
            user_id="u1",
            avatar="🦊",
            skills=["Vue", "Python"],
            github_handle="pedro-gh",
        )
        store.upsert_profile(
            user_id="bot",
            avatar="🤖",
            skills=["Testing"],
            model="gpt-4o",
            specialization="qa",
        )

        assert cursor.human["u1"]["avatar"] == "🦊"
        assert cursor.human["u1"]["github_handle"] == "pedro-gh"
        assert cursor.agents["bot"]["model"] == "gpt-4o"
        assert cursor.agents["bot"]["specialization"] == "qa"
        assert cursor.skills == {"vue": "Vue", "python": "Python", "testing": "Testing"}
        assert cursor.user_skills["u1"] == {"vue", "python"}
        assert cursor.user_skills["bot"] == {"testing"}

    def test_unknown_user_is_ignored(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)
        store.create_schema()

        store.upsert_profile(user_id="ghost", avatar="👻")

        assert cursor.human == {} and cursor.agents == {}


class TestAuthenticateUser:
    def test_roundtrip_with_joined_credential(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)
        store.create_schema()
        store.upsert_user(
            user_id="u1",
            username="Pedro.Perez",
            username_normalized="pedro.perez",
            email="pedro@socialseed.com",
            password_hash=hash_password("secreto"),
            role="developer",
            user_type="human",
            created_at=None,
        )

        record = authenticate_user("postgresql://fake", "pedro.perez", "secreto")
        assert record is not None
        assert record["id"] == "u1"
        assert record["role"] == "DEVELOPER"
        assert record["type"] == "human"
        assert record["email"] == "pedro@socialseed.com"

        assert authenticate_user("postgresql://fake", "pedro.perez", "wrong") is None
        assert authenticate_user("postgresql://fake", "unknown", "secreto") is None

    def test_agents_have_no_credential(self, monkeypatch: pytest.MonkeyPatch) -> None:
        cursor = FakePgCursor()
        store = _store(monkeypatch, cursor)
        store.create_schema()
        store.upsert_user(
            user_id="bot",
            username="bot",
            username_normalized="bot",
            email="bot@socialseed.com",
            password_hash="",
            role=None,
            user_type="agent",
            created_at=None,
        )

        assert authenticate_user("postgresql://fake", "bot", "anything") is None

    def test_empty_credentials_short_circuit_without_connect(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _fail(*args: object, **kwargs: object) -> None:
            raise AssertionError("connect must not be called")

        monkeypatch.setattr(user_store_module.psycopg, "connect", _fail)
        assert authenticate_user("postgresql://fake", "", "x") is None
        assert authenticate_user("postgresql://fake", "someone", "") is None
