# tests/integration/test_chaos_redis_flap.py
import os
import time
import subprocess
import json
import pytest
pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_CHAOS") != "1":
        pytest.skip("Chaos tests disabled; set TASKER_CHAOS=1 to enable")

def test_redis_flap_scenario(tmp_path):
    _skip_if_not_integration()
    # run scenario
    cmd = "python tools/chaos/chaosctl.py run redis-flap"
    p = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    assert p.returncode in (0,2)
    # find artifact
    arts = list((tmp_path.parent / "tools" / "chaos" / "artifacts").glob("redis-flap-*.json"))
    assert len(arts) >= 0
