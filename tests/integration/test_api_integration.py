import os
import pytest
import requests

pytestmark = pytest.mark.integration

BASE = os.getenv("TASKER_API_URL", "http://localhost:8000")
BOARD = os.getenv("TASKER_BOARD_URL", "http://localhost:8080")


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")


def test_api_health():
    _skip_if_not_integration()
    r = requests.get(f"{BASE}/health")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") in ("healthy", "degraded")


def test_api_cors_preflight():
    _skip_if_not_integration()
    headers = {"Origin": "http://localhost:8080", "Access-Control-Request-Method": "GET"}
    r = requests.options(f"{BASE}/api/v1/issues", headers=headers)
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") in ("http://localhost:8080", "*")


def test_board_health():
    _skip_if_not_integration()
    r = requests.get(f"{BOARD}/")
    assert r.status_code in (200, 301, 302)
