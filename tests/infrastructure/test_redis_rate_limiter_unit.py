from unittest.mock import MagicMock, patch

from socialseed_tasker.infrastructure.redis_rate_limiter import RedisRateLimiter


def test_redis_rate_limiter_script_registration():
    import socialseed_tasker.infrastructure.redis_rate_limiter as rl_mod
    rl_mod._REDIS_AVAILABLE = True
    client = MagicMock()
    client.register_script.return_value = lambda keys, args: [1, 1.0]
    rl_mod.redis = MagicMock()
    rl_mod.redis.from_url.return_value = client
    rl = RedisRateLimiter(redis_url="redis://localhost:6379/0", rate_per_min=60, burst=5)
    assert rl.allow("k1")
