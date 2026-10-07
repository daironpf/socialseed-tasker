"""Unit tests for the /users router: delete guard (#556) and PostgreSQL reads (#558)."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from socialseed_tasker.infrastructure.web_api.routers import user as user_router
from socialseed_tasker.infrastructure.web_api.schemas import UserResponse

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
