from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.rate_limit import BURST, USER_PER_MIN


def test_rate_limit_middleware_blocks():
    app = create_app()
    app.state.rate_limiter = MagicMock()
    app.state.rate_limiter.allow.side_effect = [True, False]
    client = TestClient(app)
    r1 = client.get("/health")
    assert r1.status_code != 429
    r2 = client.get("/health")
    assert r2.status_code == 429


def test_app_wires_rate_limiter_with_documented_limits(monkeypatch):
    """The web app must use the documented 120 req/min, burst 60 limits.

    It previously instantiated ``MemoryRateLimiter()`` with the bare 60/20
    defaults, so the documented ``TASKER_RATE_USER_PER_MIN`` /
    ``TASKER_RATE_BURST`` settings were dead code for the API and the
    frontend boot burst (~25 requests) drained the bucket, making saves
    fail with 429 (issue reported after #577).
    """
    monkeypatch.delenv("TASKER_REDIS_URL", raising=False)
    app = create_app()
    limiter = app.state.rate_limiter
    assert limiter.rate_per_min == USER_PER_MIN == 120
    assert limiter.burst == BURST == 60
