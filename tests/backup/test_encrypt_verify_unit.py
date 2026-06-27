# tests/backup/test_encrypt_verify_unit.py
import os
from socialseed_tasker.backup.core import export_data
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from unittest.mock import MagicMock

def test_export_encrypt(tmp_path):
    storage = MemoryStorage()
    issue_repo = MagicMock()
    issue_repo.list_all.return_value = []
    graph_repo = MagicMock()
    graph_repo.dump.return_value = []
    out = tmp_path / "export.tar.gz"
    passphrase = "testpass"
    path = export_data(str(out), issue_repo=issue_repo, graph_repo=graph_repo, storage=storage, include_storage=False, encrypt=True, passphrase=passphrase)
    assert path.endswith(".enc")
    assert os.path.exists(path)
