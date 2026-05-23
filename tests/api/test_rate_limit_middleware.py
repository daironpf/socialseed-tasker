from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app


def test_rate_limit_middleware_blocks():
    app = create_app()
    app.state.rate_limiter = MagicMock()
    app.state.rate_limiter.allow.side_effect = [True, False]
    client = TestClient(app)
    r1 = client.get("/health")
    assert r1.status_code != 429
    r2 = client.get("/health")
    assert r2.status_code == 429
