# tests/backup/test_export_unit.py
import tarfile
import tempfile
from unittest.mock import MagicMock

from socialseed_tasker.backup.core import export_data, verify_export
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage


def test_export_and_verify(tmp_path):
    storage = MemoryStorage()
    storage.put("k1", b"v1")
    issue_repo = MagicMock()
    issue_repo.list_all.return_value = [{"id":"i1","title":"T"}]
    graph_repo = MagicMock()
    graph_repo.dump.return_value = [{"node":"n1"}]
    out = tmp_path / "export.tar.gz"
    path = export_data(
        str(out),
        issue_repo=issue_repo,
        graph_repo=graph_repo,
        storage=storage,
        include_storage=True,
        encrypt=False,
    )
    assert path == str(out)
    assert verify_export(path)

def test_verify_export_rejects_path_traversal(tmp_path):
    payload = tmp_path / "payload.txt"
    payload.write_text("x", encoding="utf-8")
    archive = tmp_path / "evil.tar.gz"
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(payload, arcname="../escape.txt")
    assert verify_export(str(archive)) is False
