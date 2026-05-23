import os
import time

import pytest
import requests

from socialseed_tasker.observability.exporter import start_exporter
from socialseed_tasker.observability.metrics import observe_operation

pytestmark = pytest.mark.integration


def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")


def test_metrics_endpoint_exposes_metrics():
    _skip_if_not_integration()
    port = int(os.getenv("TASKER_METRICS_PORT", "8001"))
    start_exporter(port=port)
    with observe_operation("integration", "op"):
        pass
    time.sleep(0.5)
    r = requests.get(f"http://localhost:{port}/metrics")
    assert r.status_code == 200
    text = r.text
    assert "tasker_requests_total" in text
    assert "tasker_request_duration_seconds" in text
