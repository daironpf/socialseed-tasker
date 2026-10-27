from unittest.mock import MagicMock, patch

import pytest

from socialseed_tasker.application.exceptions import StorageError
from socialseed_tasker.infrastructure.redis_storage import RedisStorage


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
    with pytest.raises(StorageError):
        RedisStorage(url="redis://bad")

@patch("socialseed_tasker.infrastructure.redis_storage.redis")
def test_redis_storage_list_keys_decodes_bytes(mock_redis_module):
    client = MagicMock()
    mock_redis_module.from_url.return_value = client
    client.ping.return_value = True
    client.scan_iter.return_value = [b"one", "two"]

    storage = RedisStorage(url="redis://localhost:6379/0")

    assert storage.list_keys() == ["one", "two"]
    client.scan_iter.assert_called_once_with()

@patch("socialseed_tasker.infrastructure.redis_storage.redis")
def test_redis_storage_list_keys_wraps_scan_errors(mock_redis_module):
    client = MagicMock()
    mock_redis_module.from_url.return_value = client
    client.ping.return_value = True
    client.scan_iter.side_effect = RuntimeError("scan failed")

    storage = RedisStorage(url="redis://localhost:6379/0")

    with pytest.raises(StorageError, match="Redis key listing failed"):
        storage.list_keys()
