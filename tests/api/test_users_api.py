"""Unit tests for the /users router: delete guard (#556), PostgreSQL reads (#558)
and human creation against the normalized schema (#559)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from socialseed_tasker.infrastructure.web_api.routers import user as user_router
from socialseed_tasker.infrastructure.web_api.schemas import UserCreateRequest, UserResponse
from tests.fakes.fake_pg_users import FakePgCursor, install_fake_pg

HUMAN_PROFILE = {
    "id": "uid-ana",
    "username": "ana",
    "type": "human",
    "email": "ana@socialseed.com",
    "role": "VIEWER",
    "avatar": "🦊",
    "skills": ["python", "vue"],
    "model": None,
    "specialization": None,
    "is_active": False,
    "github_handle": "ana-gh",
    "preferences": "dark",
    "created_at": datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc),
    "last_login": datetime(2026, 10, 6, 9, 30, tzinfo=timezone.utc),
}

AGENT_PROFILE = {
    "id": "uid-bot",
    "username": "bot-qa",
    "type": "agent",
    "email": "bot@socialseed.com",
    "role": "ai-agent",
    "avatar": "🤖",
    "skills": ["testing"],
    "model": "gpt-4o",
    "specialization": "qa",
    "is_active": True,
    "github_handle": None,
    "preferences": None,
    "created_at": datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc),
    "last_login": None,
}


def _fake_repo(users: list[object]) -> MagicMock:
    repo = MagicMock()
    repo.list_users.return_value = users
    return repo


def test_delete_last_user_is_rejected():
    repo = _fake_repo([object()])
    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=repo,
    ), pytest.raises(HTTPException) as exc:
        user_router.delete_user("admin-profile", driver=object())
    assert exc.value.status_code == 409
    assert exc.value.detail == "Cannot delete the last user"
    repo.list_users.assert_called_once_with(limit=2)
    repo.delete_user.assert_not_called()


def test_delete_proceeds_when_other_users_remain():
    repo = _fake_repo([object(), object()])
    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=repo,
    ):
        response = user_router.delete_user("user-1", driver=object())
    repo.delete_user.assert_called_once_with("user-1")
    assert response.data == {"status": "deleted"}


def test_list_users_without_database_url_returns_503(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(user_router, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        user_router.list_users()

    assert exc.value.status_code == 503
    assert "TASKER_DATABASE_URL" in str(exc.value.detail)


def test_get_user_without_database_url_returns_503(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(user_router, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        user_router.get_user("uid-ana")

    assert exc.value.status_code == 503


def test_list_users_returns_full_postgresql_profiles(monkeypatch: pytest.MonkeyPatch):
    pg_repo = MagicMock()
    pg_repo.list_users.return_value = [HUMAN_PROFILE, AGENT_PROFILE]
    monkeypatch.setattr(user_router, "get_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(user_router, "PgUserRepository", MagicMock(return_value=pg_repo))

    response = user_router.list_users(role=None, limit=10)

    pg_repo.list_users.assert_called_once_with(role=None, limit=10)
    human, agent = response.data
    assert isinstance(human, UserResponse)
    assert human.id == "uid-ana"
    assert human.role == "VIEWER"
    assert human.type == "human"
    assert human.avatar == "🦊"
    assert human.skills == ["python", "vue"]
    assert human.is_active is False
    assert human.model is None
    assert human.last_login is not None
    assert agent.role == "ai-agent"
    assert agent.type == "agent"
    assert agent.model == "gpt-4o"
    assert agent.specialization == "qa"


def test_list_users_forwards_role_filter(monkeypatch: pytest.MonkeyPatch):
    pg_repo = MagicMock()
    pg_repo.list_users.return_value = []
    monkeypatch.setattr(user_router, "get_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(user_router, "PgUserRepository", MagicMock(return_value=pg_repo))

    user_router.list_users(role="ai-agent", limit=5)

    pg_repo.list_users.assert_called_once_with(role="ai-agent", limit=5)


def test_get_user_returns_profile_or_404(monkeypatch: pytest.MonkeyPatch):
    pg_repo = MagicMock()
    pg_repo.get_user.side_effect = lambda user_id: HUMAN_PROFILE if user_id == "uid-ana" else None
    monkeypatch.setattr(user_router, "get_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(user_router, "PgUserRepository", MagicMock(return_value=pg_repo))

    response = user_router.get_user("uid-ana")
    assert response.data.id == "uid-ana"
    assert response.data.role == "VIEWER"

    with pytest.raises(HTTPException) as exc:
        user_router.get_user("ghost")
    assert exc.value.status_code == 404


def test_get_user_by_email_returns_profile_or_404(monkeypatch: pytest.MonkeyPatch):
    pg_repo = MagicMock()
    pg_repo.get_user_by_email.side_effect = (
        lambda email: AGENT_PROFILE if email == "bot@socialseed.com" else None
    )
    monkeypatch.setattr(user_router, "get_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(user_router, "PgUserRepository", MagicMock(return_value=pg_repo))

    response = user_router.get_user_by_email("bot@socialseed.com")
    assert response.data.id == "uid-bot"
    assert response.data.role == "ai-agent"

    with pytest.raises(HTTPException) as exc:
        user_router.get_user_by_email("ghost@socialseed.com")
    assert exc.value.status_code == 404


def test_delete_also_removes_postgresql_row(monkeypatch: pytest.MonkeyPatch):
    neo4j_repo = _fake_repo([object(), object()])
    pg_repo = MagicMock()
    monkeypatch.setattr(user_router, "get_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(user_router, "PgUserRepository", MagicMock(return_value=pg_repo))
    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=neo4j_repo,
    ):
        response = user_router.delete_user("uid-ana", driver=object())

    assert response.data == {"status": "deleted"}
    pg_repo.delete_user_row.assert_called_once_with("uid-ana")


def test_delete_succeeds_when_postgresql_fails(monkeypatch: pytest.MonkeyPatch):
    neo4j_repo = _fake_repo([object(), object()])
    pg_repo = MagicMock()
    pg_repo.delete_user_row.side_effect = RuntimeError("connection refused")
    monkeypatch.setattr(user_router, "get_database_url", lambda: "postgresql://fake")
    monkeypatch.setattr(user_router, "PgUserRepository", MagicMock(return_value=pg_repo))
    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=neo4j_repo,
    ):
        response = user_router.delete_user("uid-ana", driver=object())

    assert response.data == {"status": "deleted"}


def test_delete_without_database_url_skips_postgresql(monkeypatch: pytest.MonkeyPatch):
    neo4j_repo = _fake_repo([object(), object()])
    pg_factory = MagicMock()
    monkeypatch.setattr(user_router, "get_database_url", lambda: None)
    monkeypatch.setattr(user_router, "PgUserRepository", pg_factory)
    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=neo4j_repo,
    ):
        response = user_router.delete_user("uid-ana", driver=object())

    assert response.data == {"status": "deleted"}
    pg_factory.assert_not_called()


# ---------------------------------------------------------------------------
# POST /users - creation over the normalized schema (issue #559)
# ---------------------------------------------------------------------------


def _install_create(monkeypatch: pytest.MonkeyPatch, cursor: FakePgCursor) -> MagicMock:
    """Route the store to the fake SQL and the read-back to composed profiles."""
    install_fake_pg(monkeypatch, cursor)
    monkeypatch.setattr(user_router, "get_database_url", lambda: "postgresql://fake")

    def _read(uid: str) -> dict | None:
        user = cursor.users.get(uid)
        if not user:
            return None
        human = cursor.human.get(uid, {})
        return {
            "id": uid,
            "username": user["username"],
            "type": "human",
            "email": human.get("email"),
            "role": human.get("role_id", "DEVELOPER"),
            "avatar": human.get("avatar"),
            "skills": sorted(cursor.skills[s] for s in cursor.user_skills.get(uid, set())),
            "model": None,
            "specialization": None,
            "is_active": human.get("is_active", True),
            "github_handle": human.get("github_handle"),
            "preferences": human.get("preferences"),
            "created_at": None,
            "last_login": None,
        }

    pg_repo = MagicMock()
    pg_repo.get_user.side_effect = _read
    monkeypatch.setattr(user_router, "PgUserRepository", MagicMock(return_value=pg_repo))
    return pg_repo


def test_create_user_201_returns_uid_and_profile(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)

    response = user_router.create_user(
        UserCreateRequest(
            username="pedro",
            email="pedro@socialseed.com",
            role="developer",
            avatar="🧑‍💻",
            skills=["Vue"],
        ),
        driver=None,
    )

    assert len(cursor.users) == 1
    uid = next(iter(cursor.users))
    assert uid.startswith("pg-gen-"), uid
    assert cursor.users[uid]["user_type"] == "human"
    human = cursor.human[uid]
    assert human["role_id"] == "DEVELOPER"
    assert human["password_hash"] == ""
    assert human["email"] == "pedro@socialseed.com"
    assert human["avatar"] == "🧑‍💻"
    assert response.data.id == uid
    assert response.data.username == "pedro"
    assert response.data.type == "human"
    assert response.data.role == "DEVELOPER"
    assert response.data.avatar == "🧑‍💻"
    assert response.data.skills == ["Vue"]


def test_create_user_persists_skills_in_user_skills(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)

    response = user_router.create_user(
        UserCreateRequest(username="ana", email="ana@x.com", role="VIEWER", skills=["Vue", "Python"]),
        driver=None,
    )

    uid = response.data.id
    assert cursor.skills == {"vue": "Vue", "python": "Python"}
    assert cursor.user_skills[uid] == {"vue", "python"}
    assert response.data.role == "VIEWER"
    assert response.data.skills == ["Python", "Vue"]


def test_create_user_duplicate_username_409(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    cursor.users["u1"] = {
        "id": "u1",
        "username": "pedro",
        "username_normalized": "pedro",
        "user_type": "human",
        "created_at": None,
    }
    _install_create(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.create_user(
            UserCreateRequest(username="Pedro", email="other@x.com", role="developer"),
            driver=None,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "username already exists"
    assert len(cursor.users) == 1


def test_create_user_duplicate_email_409(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    cursor.users["u1"] = {
        "id": "u1",
        "username": "other",
        "username_normalized": "other",
        "user_type": "human",
        "created_at": None,
    }
    cursor.human["u1"] = {"user_id": "u1", "email": "taken@x.com"}
    _install_create(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.create_user(
            UserCreateRequest(username="pedro", email="taken@x.com", role="developer"),
            driver=None,
        )

    assert exc.value.status_code == 409
    assert exc.value.detail == "email already exists"
    assert len(cursor.users) == 1


def test_create_user_invalid_role_422(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.create_user(
            UserCreateRequest(username="pedro", email="pedro@x.com", role="lead-developer"),
            driver=None,
        )

    assert exc.value.status_code == 422
    assert "invalid role" in str(exc.value.detail)
    assert "DEVELOPER" in str(exc.value.detail)
    assert cursor.users == {}


def test_create_user_rejects_agent_type_422(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.create_user(
            UserCreateRequest(username="bot", email="bot@x.com", role="developer", type="agent"),
            driver=None,
        )

    assert exc.value.status_code == 422
    assert "/agents/profiles" in str(exc.value.detail)
    assert cursor.users == {}


def test_create_user_without_database_url_returns_503(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(user_router, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        user_router.create_user(
            UserCreateRequest(username="pedro", email="pedro@x.com", role="developer"),
            driver=None,
        )

    assert exc.value.status_code == 503
    assert "TASKER_DATABASE_URL" in str(exc.value.detail)


def test_post_users_route_is_not_shadowed_by_project_router():
    """``POST /api/v1/users`` must resolve to the PG create (#559).

    ``project_router`` registers its routes before ``user_router``; the legacy
    Neo4j project-link endpoint used to occupy ``POST /users`` and shadowed it
    (found via live smoke of #559). It now lives at ``POST /projects/users``.
    """
    from socialseed_tasker.infrastructure.web_api.app import create_app

    app = create_app()

    def _post_routes(path: str) -> list:
        return [
            route
            for route in app.routes
            if getattr(route, "path", None) == path and "POST" in (getattr(route, "methods", None) or set())
        ]

    create_routes = _post_routes("/api/v1/users")
    assert len(create_routes) == 1, f"POST /users shadowed or duplicated: {create_routes}"
    assert create_routes[0].endpoint.__module__ == "socialseed_tasker.infrastructure.web_api.routers.user"

    legacy_routes = _post_routes("/api/v1/projects/users")
    assert len(legacy_routes) == 1, "legacy project-link endpoint must stay reachable"
    assert legacy_routes[0].endpoint.__module__ == "socialseed_tasker.infrastructure.web_api.routers.project"


# ---------------------------------------------------------------------------
# PUT /users/{id} - update over the normalized schema (issue #560)
# ---------------------------------------------------------------------------


def _seed_user(
    monkeypatch: pytest.MonkeyPatch,
    cursor: FakePgCursor,
    *,
    username: str = "ana",
    email: str = "ana@x.com",
    role: str = "viewer",
    skills: list[str] | None = None,
) -> str:
    response = user_router.create_user(
        UserCreateRequest(
            username=username,
            email=email,
            role=role,
            avatar="🦊",
            skills=skills or ["Vue"],
        ),
        driver=None,
    )
    assert response.data.id in cursor.users
    return response.data.id


def test_update_user_full_profile_persisted(monkeypatch: pytest.MonkeyPatch):
    from socialseed_tasker.auth.user_store import normalize_username
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)
    uid = _seed_user(monkeypatch, cursor, skills=["Vue", "Go"])

    response = user_router.update_user(
        uid,
        UserUpdateRequest(
            username="Ana García",
            email="ana.g@socialseed.com",
            role="ADMIN",
            avatar="🧑‍💻",
            skills=["Python"],
        ),
        driver=None,
    )

    user = cursor.users[uid]
    assert user["username"] == "Ana García"
    assert user["username_normalized"] == normalize_username("Ana García")
    human = cursor.human[uid]
    assert human["email"] == "ana.g@socialseed.com"
    assert human["role_id"] == "ADMIN"
    assert human["avatar"] == "🧑‍💻"
    assert human["password_hash"] == ""  # never touched (#560 notes)
    assert cursor.user_skills[uid] == {"python"}  # full replacement, not a merge
    assert response.data.username == "Ana García"
    assert response.data.email == "ana.g@socialseed.com"
    assert response.data.role == "ADMIN"
    assert response.data.avatar == "🧑‍💻"
    assert response.data.skills == ["Python"]
    assert response.data.type == "human"


def test_update_user_invalid_role_422(monkeypatch: pytest.MonkeyPatch):
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)
    uid = _seed_user(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.update_user(uid, UserUpdateRequest(role="lead-developer"), driver=None)

    assert exc.value.status_code == 422
    assert "invalid role" in str(exc.value.detail)
    assert "VIEWER" in str(exc.value.detail)
    assert cursor.human[uid]["role_id"] == "VIEWER"  # untouched


def test_update_user_not_found_404(monkeypatch: pytest.MonkeyPatch):
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.update_user("ghost", UserUpdateRequest(username="x"), driver=None)

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"
    assert cursor.users == {}


def test_update_user_duplicate_username_409(monkeypatch: pytest.MonkeyPatch):
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)
    _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")
    uid_b = _seed_user(monkeypatch, cursor, username="bea", email="bea@x.com")

    with pytest.raises(HTTPException) as exc:
        user_router.update_user(uid_b, UserUpdateRequest(username="Ana"), driver=None)

    assert exc.value.status_code == 409
    assert exc.value.detail == "username already exists"
    assert cursor.users[uid_b]["username"] == "bea"  # rollback kept the old value


def test_update_user_duplicate_email_409(monkeypatch: pytest.MonkeyPatch):
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)
    _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")
    uid_b = _seed_user(monkeypatch, cursor, username="bea", email="bea@x.com")

    with pytest.raises(HTTPException) as exc:
        user_router.update_user(uid_b, UserUpdateRequest(email="ana@x.com"), driver=None)

    assert exc.value.status_code == 409
    assert exc.value.detail == "email already exists"
    assert cursor.human[uid_b]["email"] == "bea@x.com"


def test_update_user_keeps_its_own_username_and_email(monkeypatch: pytest.MonkeyPatch):
    """Re-submitting the user's own username/email must not collide (#560)."""
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)
    uid = _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")

    response = user_router.update_user(
        uid,
        UserUpdateRequest(username="ana", email="ana@x.com", avatar="🧑‍💻"),
        driver=None,
    )

    assert response.data.username == "ana"
    assert cursor.human[uid]["avatar"] == "🧑‍💻"


def test_update_user_rejects_agent_type_422(monkeypatch: pytest.MonkeyPatch):
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)
    uid = _seed_user(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.update_user(uid, UserUpdateRequest(type="agent"), driver=None)

    assert exc.value.status_code == 422
    assert "/agents/profiles" in str(exc.value.detail)


def test_update_user_without_database_url_returns_503(monkeypatch: pytest.MonkeyPatch):
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    monkeypatch.setattr(user_router, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        user_router.update_user("uid-ana", UserUpdateRequest(username="x"), driver=None)

    assert exc.value.status_code == 503
    assert "TASKER_DATABASE_URL" in str(exc.value.detail)
