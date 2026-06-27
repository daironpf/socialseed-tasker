# tests/integration/test_tracing_integration.py
import os
import time
import requests
import pytest

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

JAEGER_UI = os.getenv("TASKER_JAEGER_URL", "http://localhost:16686")

def wait_for_jaeger(timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{JAEGER_UI}/api/services", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def test_trace_emitted_and_visible():
    _skip_if_not_integration()
    assert wait_for_jaeger(), "Jaeger not ready"
    r = requests.get("http://localhost:8000/api/v1/health", timeout=5)
    assert r.status_code == 200
    time.sleep(2)
    r2 = requests.get(f"{JAEGER_UI}/api/services", timeout=5)
    assert r2.status_code == 200
    services = r2.json()
    assert any("tasker" in s for s in services)
