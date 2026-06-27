# tests/integration/test_chaos_api_latency.py
import os
import subprocess
import pytest
pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_CHAOS") != "1":
        pytest.skip("Chaos tests disabled; set TASKER_CHAOS=1 to enable")

def test_api_latency_scenario():
    _skip_if_not_integration()
    cmd = "python tools/chaos/chaosctl.py run api-latency"
    p = subprocess.run(cmd, shell=True)
    assert p.returncode in (0,2)
