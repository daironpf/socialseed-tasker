from unittest.mock import MagicMock, patch
from socialseed_tasker.infrastructure.redis_storage import RedisStorage
from socialseed_tasker.application.exceptions import StorageError

@patch("socialseed_tasker.infrastructure.redis_storage.redis")
def test_redis_storage_put_get_delete(mock_redis_module):
    client = MagicMock()
    mock_redis_module.from_url.return_value = client
    client.ping.return_value = True
    client.get.return_value = b"v"
    rs = RedisStorage(url="redis://localhost:6379/0")
    rs.put("k", b"v", ttl_seconds=10)
    client.setex.assert_called()
    assert rs.get("k") == b"v"
    rs.delete("k")
    client.delete.assert_called_with("k")

@patch("socialseed_tasker.infrastructure.redis_storage.redis")
def test_redis_storage_connection_failure(mock_redis_module):
    mock_redis_module.from_url.side_effect = Exception("conn fail")
    try:
        RedisStorage(url="redis://bad")
        assert False, "Expected StorageError"
    except StorageError:
        pass
