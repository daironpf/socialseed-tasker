import os
import time
import pytest
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.privacy.retention_worker import RetentionWorker, AUDIT_KEY
from socialseed_tasker.privacy.policy import evaluate_policy

pytestmark = pytest.mark.integration


def _skip():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")


def test_retention_worker_archives_and_deletes():
    _skip()
    from unittest.mock import MagicMock
    container = MagicMock()
    storage = MemoryStorage()
    container.storage = storage
    issue_repo = MagicMock()
    issue_repo.list_all.return_value = [
        {"id": "old-issue", "created_at": 0, "tenant": None, "tags": []},
        {"id": "recent-issue", "created_at": int(time.time()), "tenant": None, "tags": []},
    ]
    container.issue_repo = issue_repo
    storage.put("some:key:old", b"data")
    storage.put("another:key:new", b"data")
    worker = RetentionWorker(container, interval=1)
    worker.run_once()
    assert evaluate_policy({"kind": "storage", "created_at": 0, "tenant": None, "tags": []}) is False
    assert evaluate_policy({"kind": "issue", "created_at": 0, "tenant": None, "tags": []}) is False
    audits_raw = storage.get(AUDIT_KEY)
    assert audits_raw is not None
    import json
    audits = json.loads(audits_raw.decode("utf-8"))
    assert len(audits) >= 2
    actions = [a["action"] for a in audits]
    assert "delete" in actions
