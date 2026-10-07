"""Unit tests for the Neo4j user projection: re-key and tolerant node parsing (#558)."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from socialseed_tasker.domain.entities import User, UserRole
from socialseed_tasker.infrastructure.neo4j_user_repository import (
    UserRepository,
    _node_to_user,
    _parse_role,
)

UUID_ID = "f5dcf582-0cd2-48e6-a900-69d8bb3c5cda"


class _FakeResult:
    def __init__(self, updated: int) -> None:
        self._updated = updated

    def single(self) -> dict[str, Any] | None:
        return {"updated": self._updated}


class _FakeSession:
    def __init__(self, updated: int) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._updated = updated
        self.closed = False

    def __enter__(self) -> _FakeSession:
        return self

    def __exit__(self, *exc: object) -> bool:
        self.closed = True
        return False

    def run(self, query: str, **params: Any) -> _FakeResult:
        self.calls.append((query, params))
        return _FakeResult(self._updated)


class _FakeDriver:
    def __init__(self, updated: int = 0) -> None:
        self.session_calls = 0
        self._session: _FakeSession | None = None
        self._updated = updated

    @property
    def session(self) -> Any:
        def _open(database: str | None = None) -> _FakeSession:
            self.session_calls += 1
            self._session = _FakeSession(self._updated)
            return self._session

        return _open


class TestRekeyUserIds:
    def test_empty_pairs_do_not_touch_the_graph(self) -> None:
        driver = _FakeDriver()

        assert UserRepository(driver).rekey_user_ids([]) == 0
        assert driver.session_calls == 0

    def test_rekeys_nodes_by_username_and_returns_updated_count(self) -> None:
        driver = _FakeDriver(updated=2)

        updated = UserRepository(driver).rekey_user_ids([("admin", "admin"), ("bot", "uid-bot")])

        assert updated == 2
        assert driver.session_calls == 1
        session = driver._session
        assert session is not None and session.closed is True
        query, params = session.calls[0]
        assert "UNWIND $pairs AS pair" in query
        assert "MATCH (u:User {username: pair.username})" in query
        assert "WHERE u.id <> pair.id" in query
        assert "SET u.id = pair.id" in query
        assert params["pairs"] == [
            {"username": "admin", "id": "admin"},
            {"username": "bot", "id": "uid-bot"},
        ]

    def test_handles_result_without_record(self) -> None:
        class _NoRecordResult:
            def single(self) -> dict[str, Any] | None:
                return None

        class _SilentSession(_FakeSession):
            def run(self, query: str, **params: Any) -> _NoRecordResult:
                return _NoRecordResult()

        class _SilentDriver(_FakeDriver):
            @property
            def session(self) -> Any:
                def _open(database: str | None = None) -> _SilentSession:
                    self.session_calls += 1
                    return _SilentSession(0)

                return _open

        assert UserRepository(_SilentDriver()).rekey_user_ids([("admin", "admin")]) == 0


class TestParseRole:
    def test_canonical_roles_pass_through(self) -> None:
        assert _parse_role("ADMIN") is UserRole.ADMIN
        assert _parse_role("developer") is UserRole.DEVELOPER
        assert _parse_role("viewer") is UserRole.VIEWER

    def test_unknown_and_missing_roles_fall_back_to_developer(self) -> None:
        assert _parse_role("lead-developer") is UserRole.DEVELOPER
        assert _parse_role(None) is UserRole.DEVELOPER
        assert _parse_role("") is UserRole.DEVELOPER


class TestNodeToUser:
    def _node(self, **overrides: Any) -> dict[str, Any]:
        node: dict[str, Any] = {
            "id": UUID_ID,
            "username": "admin",
            "email": "admin@socialseed.com",
            "role": "ADMIN",
            "githubHandle": "admin-gh",
            "createdAt": "2026-10-01T08:00:00+00:00",
            "lastLogin": "2026-10-06T09:30:00+00:00",
            "preferences": "dark",
        }
        node.update(overrides)
        return node

    def test_parses_canonical_uuid_id(self) -> None:
        user = _node_to_user(self._node())
        assert user.id == UUID(UUID_ID)
        assert user.role is UserRole.ADMIN
        assert user.email == "admin@socialseed.com"
        assert user.github_handle == "admin-gh"
        assert user.preferences == "dark"

    def test_keeps_non_uuid_pg_uid_as_string(self) -> None:
        user = _node_to_user(self._node(id="admin"))
        assert user.id == "admin"

    def test_unknown_legacy_role_does_not_raise(self) -> None:
        user = _node_to_user(self._node(role="lead-developer"))
        assert user.role is UserRole.DEVELOPER

    def test_missing_role_does_not_raise(self) -> None:
        node = self._node()
        node.pop("role")
        user = _node_to_user(node)
        assert user.role is UserRole.DEVELOPER

    def test_missing_created_at_falls_back_to_now(self) -> None:
        node = self._node()
        node.pop("createdAt")
        user = _node_to_user(node)
        assert user.created_at is not None


class TestUserIdCoercion:
    def test_uuid_string_is_coerced_to_uuid(self) -> None:
        user = User(username="ana", id=UUID_ID)
        assert user.id == UUID(UUID_ID)

    def test_deterministic_uid_stays_string(self) -> None:
        user = User(username="admin", id="admin")
        assert user.id == "admin"

    def test_default_id_is_uuid(self) -> None:
        user = User(username="ana")
        assert isinstance(user.id, UUID)
