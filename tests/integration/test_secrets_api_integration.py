import base64
import os
import time

import pytest

pytestmark = pytest.mark.integration


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_api_put_rotate_and_audit():
    _skip_if_not_integration()
    import requests

    base = "http://localhost:8000"
    headers = {"Authorization": "Bearer admin"}
    val = base64.b64encode(b"initval").decode("utf-8")
    r = requests.post(
        f"{base}/api/v1/secrets",
        json={
            "name": "itest",
            "value": val,
            "metadata": {"owner": "ci"},
        },
        timeout=5,
        headers=headers,
    )
    assert r.status_code == 200
    r2 = requests.post(
        f"{base}/api/v1/secrets/rotate",
        json={
            "name": "itest",
            "interval_seconds": 1,
            "policy": {"strategy": "random", "length": 8},
        },
        timeout=5,
        headers=headers,
    )
    assert r2.status_code == 200
    rid = r2.json().get("rotation_id")
    r3 = requests.post(
        f"{base}/api/v1/secrets/rotate/run",
        json={"rotation_id": rid},
        timeout=5,
        headers=headers,
    )
    assert r3.status_code == 200
    r4 = requests.get(
        f"{base}/api/v1/secrets/audit", timeout=5, headers=headers
    )
    assert r4.status_code == 200
    assert len(r4.json().get("audit", [])) >= 2
