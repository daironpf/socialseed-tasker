import os
import time
import requests
import pytest

pytestmark = pytest.mark.integration


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_rate_limit_with_redis():
    _skip_if_not_integration()
    base = "http://localhost:8000"
    headers = {"Authorization": "Bearer admintoken123"}
    allowed = 0
    for i in range(10):
        r = requests.get(f"{base}/api/v1/issues/some", headers=headers)
        if r.status_code != 429:
            allowed += 1
        time.sleep(0.05)
    assert allowed <= int(os.getenv("TASKER_RATE_USER_PER_MIN", "120"))
