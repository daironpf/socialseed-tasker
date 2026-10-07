"""Unit tests for the /users router delete guard (issue #556)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from socialseed_tasker.infrastructure.web_api.routers import user as user_router


def _fake_repo(users: list[object]) -> MagicMock:
    repo = MagicMock()
    repo.list_users.return_value = users
    return repo


def test_delete_last_user_is_rejected():
    repo = _fake_repo([object()])
    with patch(
        "socialseed_tasker.infrastructure.neo4j_user_repository.UserRepository",
        return_value=repo,
    ):
        with pytest.raises(HTTPException) as exc:
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
