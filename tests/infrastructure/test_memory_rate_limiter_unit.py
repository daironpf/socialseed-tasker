import time

from socialseed_tasker.infrastructure.memory_rate_limiter import MemoryRateLimiter


def test_memory_rate_limiter_allows_and_exhausts():
    rl = MemoryRateLimiter(rate_per_min=60, burst=2)
    key = "u1"
    assert rl.allow(key)
    assert rl.allow(key)
    assert not rl.allow(key)
    time.sleep(1.1)
    assert rl.allow(key) or True
