import os
import time
import pytest
from socialseed_tasker.infrastructure.redis_storage import RedisStorage

pytestmark = pytest.mark.integration

def _skip_if_no_redis():
    if os.getenv("TASKER_REDIS_URL") is None:
        pytest.skip("Redis not configured; set TASKER_REDIS_URL or run compose/infra/redis.yml")

def test_redis_put_get_delete_integration():
    _skip_if_no_redis()
    url = os.getenv("TASKER_REDIS_URL", "redis://localhost:6379/0")
    s = RedisStorage(url=url)
    s.put("ik", b"iv", ttl_seconds=2)
    assert s.get("ik") == b"iv"
    time.sleep(2.1)
    assert s.get("ik") is None
    s.put("ik2", b"v2")
    assert s.get("ik2") == b"v2"
    s.delete("ik2")
    assert s.get("ik2") is None
