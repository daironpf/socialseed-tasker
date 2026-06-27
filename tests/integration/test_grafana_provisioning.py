import os
import time
import requests
import pytest

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")

GRAFANA_URL = os.getenv("TASKER_GRAFANA_URL", "http://localhost:3000")
PROM_URL = os.getenv("TASKER_PROM_URL", "http://localhost:9090")

def wait_for(url, timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code < 500:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def test_grafana_and_prometheus_provisioned():
    _skip_if_not_integration()
    assert wait_for(f"{PROM_URL}/-/ready"), "Prometheus not ready"
    assert wait_for(f"{GRAFANA_URL}/api/health"), "Grafana not ready"
    # verify dashboard exists via Grafana search API
    r = requests.get(f"{GRAFANA_URL}/api/search?query=Tasker%20Overview", auth=("admin","admin"), timeout=5)
    assert r.status_code == 200
    items = r.json()
    assert any(item.get("title") == "Tasker Overview" or item.get("uid") == "tasker-overview" for item in items)
    # verify Prometheus has metric (may be empty but endpoint should respond)
    r2 = requests.get(f"{PROM_URL}/api/v1/targets", timeout=5)
    assert r2.status_code == 200
    targets = r2.json()
    assert "data" in targets
