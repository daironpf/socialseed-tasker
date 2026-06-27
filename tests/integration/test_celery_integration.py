import os
import time
import json
import subprocess
import sys
import pytest
from socialseed_tasker.workers.app import create_celery

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")

def test_enqueue_and_run_parse_task():
    _skip_if_not_integration()
    celery = create_celery()
    import tempfile
    p = tempfile.NamedTemporaryFile(suffix=".py", delete=False)
    p.write(b"def f():\n    return 1\n")
    p.flush()
    p.close()
    task = celery.send_task("tasker.parse_and_index_files", args=[[p.name]])
    for _ in range(60):
        res = celery.AsyncResult(task.id)
        if res.ready():
            break
        time.sleep(0.5)
    assert res.ready()
    assert isinstance(res.result, dict)
