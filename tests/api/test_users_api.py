"""Unit tests for the /users router: delete guard (#556), PostgreSQL reads (#558)
and human creation against the normalized schema (#559)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

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


# ---------------------------------------------------------------------------
# DELETE /users/{id} - root delete with cascade (issue #562)
# ---------------------------------------------------------------------------


def _install_delete(monkeypatch: pytest.MonkeyPatch, cursor: FakePgCursor) -> MagicMock:
    """Profile reads come from the composed fake; guard/delete run real SQL on the fake cursor."""
    from socialseed_tasker.infrastructure.pg_user_repository import PgUserRepository as RealPgRepository

    pg_repo = _install_create(monkeypatch, cursor)
    pg_repo.count_humans.side_effect = lambda: RealPgRepository("postgresql://fake").count_humans()
    pg_repo.delete_user_row.side_effect = lambda uid: RealPgRepository("postgresql://fake").delete_user_row(uid)
    return pg_repo


async def test_delete_last_human_counts_postgres_and_returns_409(monkeypatch: pytest.MonkeyPatch):
    """The guard counts humans in the PG root, not Neo4j (#562)."""
    cursor = FakePgCursor()
    _install_delete(monkeypatch, cursor)
    uid = _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")

    with pytest.raises(HTTPException) as exc:
        await user_router.delete_user(uid, request=MagicMock(), driver=object())

    assert exc.value.status_code == 409
    assert exc.value.detail == "Cannot delete the last user"
    assert uid in cursor.users  # nothing was deleted


async def test_delete_agent_skips_the_human_guard(monkeypatch: pytest.MonkeyPatch):
    """Agents are not subject to the last-human guard (#562 notes)."""
    cursor = FakePgCursor()
    _install_delete(monkeypatch, cursor)
    _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")  # the only human
    cursor.users["uid-bot"] = {
        "id": "uid-bot",
        "username": "bot-qa",
        "username_normalized": "bot.qa",
        "user_type": "agent",
        "created_at": None,
    }
    cursor.agents["uid-bot"] = {"user_id": "uid-bot", "email": "bot@x.com"}

    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=_fake_repo([object(), object()]),
    ):
        response = await user_router.delete_user("uid-bot", request=MagicMock(), driver=object())

    assert response.data == {"status": "deleted"}
    assert "uid-bot" not in cursor.users


async def test_delete_user_removes_postgres_credential(monkeypatch: pytest.MonkeyPatch):
    """After DELETE the row is gone and authenticate_user can no longer match it (#562)."""
    from socialseed_tasker.auth.user_store import authenticate_user, hash_password

    cursor = FakePgCursor()
    _install_delete(monkeypatch, cursor)
    _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")
    uid = _seed_user(monkeypatch, cursor, username="boss", email="boss@x.com", role="admin")
    cursor.human[uid]["password_hash"] = hash_password("sesamo")

    before = authenticate_user("postgresql://fake", "boss", "sesamo")
    assert before is not None and before["id"] == uid

    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=_fake_repo([object(), object()]),
    ):
        response = await user_router.delete_user(uid, request=MagicMock(), driver=object())

    assert response.data == {"status": "deleted"}
    assert uid not in cursor.users
    assert uid not in cursor.human
    assert authenticate_user("postgresql://fake", "boss", "sesamo") is None


async def test_delete_proceeds_when_other_users_remain(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_delete(monkeypatch, cursor)
    _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")
    uid = _seed_user(monkeypatch, cursor, username="bea", email="bea@x.com")
    neo4j_repo = _fake_repo([object(), object()])

    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=neo4j_repo,
    ):
        response = await user_router.delete_user(uid, request=MagicMock(), driver=object())

    assert response.data == {"status": "deleted"}
    neo4j_repo.delete_user.assert_called_once_with(uid)
    assert uid not in cursor.users  # root row really removed, not just logged


async def test_delete_user_cleans_projections(monkeypatch: pytest.MonkeyPatch):
    """Neo4j + Mongo cleanups are invoked and their failures never break the 200 (#562)."""
    cursor = FakePgCursor()
    _install_delete(monkeypatch, cursor)
    _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")
    uid = _seed_user(monkeypatch, cursor, username="bea", email="bea@x.com")
    neo4j_repo = _fake_repo([object(), object()])
    neo4j_repo.delete_user.side_effect = RuntimeError("neo4j down")
    mongo_factory = MagicMock()
    mongo_factory.return_value.clear_all = AsyncMock(side_effect=RuntimeError("mongo down"))
    monkeypatch.setattr(user_router, "NotificationMongoRepository", mongo_factory)

    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=neo4j_repo,
    ):
        response = await user_router.delete_user(uid, request=MagicMock(), driver=object())

    assert response.data == {"status": "deleted"}
    neo4j_repo.delete_user.assert_called_once_with(uid)
    mongo_factory.return_value.clear_all.assert_awaited_once_with(uid)
    assert uid not in cursor.users  # the root delete is the guaranteed effect


async def test_delete_fails_when_postgresql_fails(monkeypatch: pytest.MonkeyPatch):
    """The root delete is authoritative: a PG failure must not look like success (#562)."""
    cursor = FakePgCursor()
    pg_repo = _install_delete(monkeypatch, cursor)
    _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")
    uid = _seed_user(monkeypatch, cursor, username="bea", email="bea@x.com")
    pg_repo.delete_user_row.side_effect = RuntimeError("connection refused")

    with pytest.raises(HTTPException) as exc:
        await user_router.delete_user(uid, request=MagicMock(), driver=None)

    assert exc.value.status_code == 500
    assert exc.value.detail == "PostgreSQL user delete failed"
    assert uid in cursor.users


async def test_delete_without_database_url_returns_503(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(user_router, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        await user_router.delete_user("uid-ana", request=MagicMock(), driver=None)

    assert exc.value.status_code == 503
    assert "TASKER_DATABASE_URL" in str(exc.value.detail)


async def test_delete_not_found_404(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install_delete(monkeypatch, cursor)
    _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")

    with pytest.raises(HTTPException) as exc:
        await user_router.delete_user("ghost", request=MagicMock(), driver=object())

    assert exc.value.status_code == 404
    assert exc.value.detail == "User not found"


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
            "type": user.get("user_type", "human"),
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
        request=MagicMock(),
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
        user_router.update_user(uid, UserUpdateRequest(role="lead-developer"), request=MagicMock(), driver=None)

    assert exc.value.status_code == 422
    assert "invalid role" in str(exc.value.detail)
    assert "VIEWER" in str(exc.value.detail)
    assert cursor.human[uid]["role_id"] == "VIEWER"  # untouched


def test_update_user_not_found_404(monkeypatch: pytest.MonkeyPatch):
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    cursor = FakePgCursor()
    _install_create(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        user_router.update_user("ghost", UserUpdateRequest(username="x"), request=MagicMock(), driver=None)

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
        user_router.update_user(uid_b, UserUpdateRequest(username="Ana"), request=MagicMock(), driver=None)

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
        user_router.update_user(uid_b, UserUpdateRequest(email="ana@x.com"), request=MagicMock(), driver=None)

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
        request=MagicMock(),
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
        user_router.update_user(uid, UserUpdateRequest(type="agent"), request=MagicMock(), driver=None)

    assert exc.value.status_code == 422
    assert "/agents/profiles" in str(exc.value.detail)


def test_update_user_without_database_url_returns_503(monkeypatch: pytest.MonkeyPatch):
    from socialseed_tasker.infrastructure.web_api.schemas import UserUpdateRequest

    monkeypatch.setattr(user_router, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        user_router.update_user("uid-ana", UserUpdateRequest(username="x"), request=MagicMock(), driver=None)

    assert exc.value.status_code == 503
    assert "TASKER_DATABASE_URL" in str(exc.value.detail)


# ---------------------------------------------------------------------------
# PUT /users/{id} - session revocation on role change (issue #561)
# ---------------------------------------------------------------------------


def _install_role_env(
    monkeypatch: pytest.MonkeyPatch,
    cursor: FakePgCursor,
    password: str = "sesamo",
) -> TestClient:
    """Full app + fake PostgreSQL and a password login reading the fake credential (#561)."""
    from socialseed_tasker.auth.user_store import normalize_username
    from socialseed_tasker.infrastructure.web_api.app import create_app

    _install_delete(monkeypatch, cursor)
    monkeypatch.setattr(
        "socialseed_tasker.infrastructure.web_api.routers.auth.get_database_url",
        lambda: "postgresql://fake",
    )
    monkeypatch.delenv("TASKER_AUTH_ENABLED", raising=False)
    monkeypatch.delenv("TASKER_API_KEY", raising=False)
    monkeypatch.delenv("TASKER_REDIS_URL", raising=False)

    def _fake_authenticate(_url: str, username: str, candidate: str) -> dict | None:
        normalized = normalize_username(username)
        for row in cursor.users.values():
            if row["username_normalized"] != normalized:
                continue
            human = cursor.human.get(row["id"], {})
            if not human.get("password_hash") or candidate != password:
                return None
            return {
                "id": row["id"],
                "username": row["username"],
                "email": human.get("email"),
                "role": human.get("role_id"),
                "type": row["user_type"],
            }
        return None

    monkeypatch.setattr(
        "socialseed_tasker.infrastructure.web_api.routers.auth.authenticate_user",
        _fake_authenticate,
    )
    return TestClient(create_app())


def _login(client: TestClient, username: str, password: str) -> dict:
    resp = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_role_change_revokes_sessions_and_new_login_has_new_role(
    monkeypatch: pytest.MonkeyPatch,
):
    cursor = FakePgCursor()
    client = _install_role_env(monkeypatch, cursor)
    uid = _seed_user(monkeypatch, cursor, username="boss", email="boss@x.com", role="admin")
    cursor.human[uid]["password_hash"] = "$2b$12$fakehash"  # credentialed user (#563 pendiente)

    first = _login(client, "boss", "sesamo")
    assert first["user"]["role"] == "ADMIN"
    assert client.app.state.auth_sessions.backend == "memory"  # degrada sin Redis (#561)

    put = client.put(f"/api/v1/users/{uid}", json={"role": "DEVELOPER"})
    assert put.status_code == 200, put.text
    assert cursor.human[uid]["role_id"] == "DEVELOPER"

    stale_access = {"Authorization": f"Bearer {first['access_token']}"}
    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert refresh.status_code == 401  # sesion y jti revocadas
    assert client.get("/api/v1/auth/me", headers=stale_access).status_code == 401

    second = _login(client, "boss", "sesamo")
    assert second["user"]["role"] == "DEVELOPER"
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {second['access_token']}"})
    assert me.status_code == 200
    assert me.json()["role"] == "DEVELOPER"


def test_role_change_without_role_field_keeps_sessions(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    client = _install_role_env(monkeypatch, cursor)
    uid = _seed_user(monkeypatch, cursor, username="bea", email="bea@x.com", role="viewer")
    cursor.human[uid]["password_hash"] = "$2b$12$fakehash"

    first = _login(client, "bea", "sesamo")
    refresh_token = first["refresh_token"]

    put_profile = client.put(f"/api/v1/users/{uid}", json={"avatar": "🧑‍💻"})
    assert put_profile.status_code == 200, put_profile.text
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert rotated.status_code == 200  # solo perfil: no revoca nada

    put_same_role = client.put(f"/api/v1/users/{uid}", json={"role": "viewer"})
    assert put_same_role.status_code == 200, put_same_role.text
    refresh_token = rotated.json()["refresh_token"]
    rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert rotated.status_code == 200  # rol con el mismo valor: no revoca

    put_other_role = client.put(f"/api/v1/users/{uid}", json={"role": "DEVELOPER"})
    assert put_other_role.status_code == 200, put_other_role.text
    refresh_token = rotated.json()["refresh_token"]
    rejected = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert rejected.status_code == 401  # cambio efectivo: si revoca


def test_delete_user_revokes_sessions(monkeypatch: pytest.MonkeyPatch):
    """DELETE kills refresh and access for the uid, unconditionally (#562)."""
    cursor = FakePgCursor()
    client = _install_role_env(monkeypatch, cursor)
    mongo_factory = MagicMock()
    mongo_factory.return_value.clear_all = AsyncMock(return_value=1)
    monkeypatch.setattr(user_router, "NotificationMongoRepository", mongo_factory)
    _seed_user(monkeypatch, cursor, username="ana", email="ana@x.com")  # second human, guard passes
    uid = _seed_user(monkeypatch, cursor, username="boss", email="boss@x.com", role="admin")
    cursor.human[uid]["password_hash"] = "$2b$12$fakehash"

    first = _login(client, "boss", "sesamo")
    access = {"Authorization": f"Bearer {first['access_token']}"}
    assert client.get("/api/v1/auth/me", headers=access).status_code == 200

    deleted = client.delete(f"/api/v1/users/{uid}")
    assert deleted.status_code == 200, deleted.text

    refresh = client.post("/api/v1/auth/refresh", json={"refresh_token": first["refresh_token"]})
    assert refresh.status_code == 401
    assert client.get("/api/v1/auth/me", headers=access).status_code == 401
    relogin = client.post("/api/v1/auth/login", json={"username": "boss", "password": "sesamo"})
    assert relogin.status_code == 401  # credential row is gone too (#562)
