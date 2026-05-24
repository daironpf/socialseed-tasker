import os
import time

import pytest
import requests

pytestmark = pytest.mark.integration


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_graph_updates_after_dependency_added():
    _skip_if_not_integration()
    base = "http://localhost:8082"
    r = requests.get(f"{base}/api/v1/graph", timeout=5)
    assert r.status_code == 200
    r2 = requests.post(
        "http://localhost:8000/api/v1/dependencies",
        json={"from": "i1", "to": "i2", "relation": "DEPENDS_ON"},
        timeout=5,
    )
    time.sleep(1)
    r3 = requests.get(f"{base}/api/v1/graph", timeout=5)
    assert r3.status_code == 200
