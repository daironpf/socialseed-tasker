import json
from unittest.mock import MagicMock, patch

from socialseed_tasker.auth.oauth import exchange_code_for_tokens, handle_oauth_callback, SessionStore
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage


@patch("socialseed_tasker.auth.oauth.requests.post")
def test_exchange_code_for_tokens(mock_post):
    mock_post.return_value = MagicMock(status_code=200, json=lambda: {"access_token": "a", "id_token": "b", "refresh_token": "r"})
    tokens = exchange_code_for_tokens("code", "http://localhost:8000/auth/callback")
    assert "access_token" in tokens


def test_session_store_create_get_delete():
    storage = MemoryStorage()
    ss = SessionStore(storage)
    sid = ss.create({"foo": "bar"}, ttl=10)
    assert ss.get(sid)["foo"] == "bar"
    ss.delete(sid)
    assert ss.get(sid) is None
