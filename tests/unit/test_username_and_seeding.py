from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from socialseed_tasker.auth import user_store as user_store_module
from socialseed_tasker.auth.user_store import (
    hash_password,
    normalize_username,
    seed_auth_users,
    seed_users,
    verify_password,
)


class FakeUserStore:
    """In-memory stand-in for PostgresUserStore (ON CONFLICT DO NOTHING semantics)."""

    def __init__(self, database_url: str | None = None) -> None:
        self.database_url = database_url
        self.rows: dict[str, dict[str, Any]] = {}
        self.upsert_calls = 0

    def create_schema(self) -> None:
        pass

    def existing_usernames(self) -> set[str]:
        return set(self.rows)

    def upsert_user(
        self,
        *,
        user_id: str,
        username: str,
        username_normalized: str,
        email: str | None,
        password_hash: str,
        role: str | None,
        user_type: str | None,
        created_at: str | None,
    ) -> str:
        self.upsert_calls += 1
        if username_normalized in self.rows:
            return "existing"
        self.rows[username_normalized] = {
            "id": user_id,
            "username": username,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "type": user_type,
            "created_at": created_at,
        }
        return "created"


def _write_users_file(path: Path, users: list[dict[str, Any]]) -> Path:
    path.write_text(json.dumps({"users": users}), encoding="utf-8")
    return path


def _dataset_user(uid: str, username: str) -> dict[str, Any]:
    return {
        "id": uid,
        "username": username,
        "email": f"{username}@socialseed.com",
        "role": "developer",
        "type": "human",
        "created_at": "2026-01-15T10:00:00Z",
    }


class TestNormalizeUsername:
    def test_lowercases(self) -> None:
        assert normalize_username("Pedro") == "pedro"

    def test_trims_surrounding_spaces(self) -> None:
        assert normalize_username("  juan  ") == "juan"

    def test_keeps_dots_and_digits(self) -> None:
        assert normalize_username("Juan.Perez99") == "juan.perez99"

    def test_removes_hyphens(self) -> None:
        assert normalize_username("agent-architect") == "agentarchitect"

    def test_removes_hyphens_and_uppercase(self) -> None:
        assert normalize_username("lucas-agent-XXzz") == "lucasagentxxzz"

    def test_removes_internal_spaces(self) -> None:
        assert normalize_username("a b c") == "abc"

    def test_removes_special_characters(self) -> None:
        assert normalize_username("admin@#$%!") == "admin"

    def test_removes_non_ascii(self) -> None:
        assert normalize_username("josé") == "jos"

    def test_empty_stays_empty(self) -> None:
        assert normalize_username("") == ""


class TestPasswordHashing:
    def test_hash_is_bcrypt_and_not_plaintext(self) -> None:
        h = hash_password("admin")
        assert h.startswith("$2")
        assert h != "admin"

    def test_verify_roundtrip(self) -> None:
        h = hash_password("juan.perez")
        assert verify_password("juan.perez", h) is True
        assert verify_password("wrong", h) is False


class FakeUserStoreWithProfile(FakeUserStore):
    """Fake store also recording ``upsert_profile`` calls (issue #558)."""

    def __init__(self, database_url: str | None = None) -> None:
        super().__init__(database_url)
        self.profiles: list[dict[str, Any]] = []

    def upsert_profile(self, **profile: Any) -> None:
        self.profiles.append(profile)


class TestSeedUsers:
    def test_seeds_dataset_with_normalized_passwords(self, tmp_path: Path) -> None:
        users_file = _write_users_file(
            tmp_path / "users.json",
            [_dataset_user("u1", "Admin"), _dataset_user("u2", "juan.perez")],
        )
        store = FakeUserStore()
        stats = seed_users(store, users_file)
        assert stats == {"total": 2, "created": 2, "existing": 0}
        assert set(store.rows) == {"admin", "juan.perez"}
        assert store.rows["admin"]["username"] == "Admin"
        assert verify_password("admin", store.rows["admin"]["password_hash"]) is True
        assert verify_password("juan.perez", store.rows["juan.perez"]["password_hash"]) is True

    def test_enriches_profile_when_store_supports_it(self, tmp_path: Path) -> None:
        agent = {
            "id": "agent-1",
            "username": "bot-qa",
            "email": "bot@socialseed.com",
            "role": None,
            "type": "agent",
            "avatar": "🤖",
            "skills": ["testing"],
            "model": "gpt-4o",
            "specialization": "qa",
            "created_at": "2026-01-15T10:00:00Z",
        }
        human = _dataset_user("u1", "pedro")
        users_file = _write_users_file(tmp_path / "users.json", [human, agent])
        store = FakeUserStoreWithProfile()

        stats = seed_users(store, users_file)

        assert stats == {"total": 2, "created": 2, "existing": 0}
        assert store.profiles == [
            {
                "user_id": "u1",
                "avatar": None,
                "skills": None,
                "model": None,
                "specialization": None,
            },
            {
                "user_id": "agent-1",
                "avatar": "🤖",
                "skills": ["testing"],
                "model": "gpt-4o",
                "specialization": "qa",
            },
        ]

    def test_does_not_touch_profile_for_existing_users(self, tmp_path: Path) -> None:
        users_file = _write_users_file(tmp_path / "users.json", [_dataset_user("u1", "pedro")])
        store = FakeUserStoreWithProfile()

        seed_users(store, users_file)
        seed_users(store, users_file)

        assert len(store.profiles) == 1

    def test_seeding_is_idempotent(self, tmp_path: Path) -> None:
        users_file = _write_users_file(
            tmp_path / "users.json",
            [_dataset_user("u1", "pedro"), _dataset_user("u2", "agent-architect")],
        )
        store = FakeUserStore()
        first = seed_users(store, users_file)
        second = seed_users(store, users_file)
        assert first == {"total": 2, "created": 2, "existing": 0}
        assert second == {"total": 2, "created": 0, "existing": 2}
        assert len(store.rows) == 2
        assert store.upsert_calls == 2

    def test_upsert_conflict_returns_existing(self) -> None:
        store = FakeUserStore()
        kwargs: dict[str, Any] = dict(
            user_id="u1",
            username="pedro",
            username_normalized="pedro",
            email="pedro@socialseed.com",
            password_hash=hash_password("pedro"),
            role="developer",
            user_type="human",
            created_at="2026-01-15T10:00:00Z",
        )
        assert store.upsert_user(**kwargs) == "created"
        assert store.upsert_user(**kwargs) == "existing"

    def test_missing_users_key_yields_empty_stats(self, tmp_path: Path) -> None:
        users_file = tmp_path / "users.json"
        users_file.write_text("{}", encoding="utf-8")
        store = FakeUserStore()
        assert seed_users(store, users_file) == {"total": 0, "created": 0, "existing": 0}


class TestSeedAuthUsersEnv:
    def test_returns_none_without_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("TASKER_DATABASE_URL", raising=False)
        assert seed_auth_users() is None

    def test_uses_env_path_and_database_url(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        users_file = _write_users_file(tmp_path / "users.json", [_dataset_user("u1", "pedro")])
        fake = FakeUserStore()
        created: dict[str, str] = {}

        def _fake_cls(database_url: str) -> FakeUserStore:
            created["url"] = database_url
            fake.database_url = database_url
            return fake

        monkeypatch.setenv("TASKER_DATABASE_URL", "postgresql://tasker:tasker@tasker-db-pg:5432/tasker")
        monkeypatch.setenv("TASKER_AUTH_SEED_PATH", str(users_file))
        monkeypatch.setattr(user_store_module, "PostgresUserStore", _fake_cls)
        stats = seed_auth_users()
        assert stats == {"total": 1, "created": 1, "existing": 0}
        assert created["url"] == "postgresql://tasker:tasker@tasker-db-pg:5432/tasker"
        assert "pedro" in fake.rows


class _FakeWipeCursor:
    def __init__(self, tables: list[str]) -> None:
        self._tables = tables
        self.statements: list[str] = []

    def __enter__(self) -> _FakeWipeCursor:
        return self

    def __exit__(self, *exc: object) -> bool:
        return False

    def execute(self, sql: str) -> None:
        self.statements.append(sql)

    def fetchall(self) -> list[tuple[str, ...]]:
        return [(name,) for name in self._tables]


class _FakeWipeConnection:
    def __init__(self, tables: list[str]) -> None:
        self.fake_cursor = _FakeWipeCursor(tables)
        self.closed = False

    def cursor(self) -> _FakeWipeCursor:
        return self.fake_cursor

    def close(self) -> None:
        self.closed = True


class TestWipePostgresData:
    def test_truncates_every_public_table(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from socialseed_tasker.auth.user_store import wipe_postgres_data

        conn = _FakeWipeConnection(["users", "audit_log"])
        monkeypatch.setattr(user_store_module, "get_database_url", lambda: "postgresql://fake")
        monkeypatch.setattr(
            user_store_module.psycopg,
            "connect",
            lambda url, autocommit=False: conn,
        )
        assert wipe_postgres_data() == 2
        assert conn.closed is True
        statements = conn.fake_cursor.statements
        assert statements[0] == "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
        assert statements[1] == 'TRUNCATE TABLE "users", "audit_log" RESTART IDENTITY CASCADE'

    def test_returns_zero_without_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from socialseed_tasker.auth.user_store import wipe_postgres_data

        def _fail_connect(*args: object, **kwargs: object) -> None:
            raise AssertionError("connect must not be called without TASKER_DATABASE_URL")

        monkeypatch.setattr(user_store_module, "get_database_url", lambda: None)
        monkeypatch.setattr(user_store_module.psycopg, "connect", _fail_connect)
        assert wipe_postgres_data() == 0
