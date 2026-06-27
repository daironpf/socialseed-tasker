# tests/integration/test_backup_restore_integration.py
import os
import pytest
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.backup.core import export_data, verify_export, restore_data
from unittest.mock import MagicMock

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

def test_backup_restore_cycle(tmp_path):
    _skip_if_not_integration()
    storage = MemoryStorage()
    storage.put("k1", b"v1")
    issue_repo = MagicMock()
    issue_repo.list_all.return_value = [{"id":"i1","title":"T"}]
    graph_repo = MagicMock()
    graph_repo.dump.return_value = [{"node":"n1"}]
    out = tmp_path / "export.tar.gz"
    path = export_data(str(out), issue_repo=issue_repo, graph_repo=graph_repo, storage=storage, include_storage=True, encrypt=False)
    assert verify_export(path)
    storage.delete("k1")
    assert storage.get("k1") is None
    restore_data(path, issue_repo=issue_repo, graph_repo=graph_repo, storage=storage)
    assert storage.get("k1") == b"v1"
