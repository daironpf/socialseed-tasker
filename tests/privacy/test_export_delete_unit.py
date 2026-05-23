from __future__ import annotations
import os
from unittest.mock import MagicMock, patch
from socialseed_tasker.privacy.handlers import export_subject, delete_subject


class Args:
    pass


def _mock_container():
    c = MagicMock()
    c.issue_repo = MagicMock(spec=["list_all", "delete"])
    c.issue_repo.list_all.return_value = [
        {"id": "issue-1", "owner": "user1", "title": "A"},
        {"id": "issue-2", "owner": "user2", "title": "B"},
    ]
    c.issue_repo.delete.return_value = None
    c.storage.list_keys.return_value = [
        "subject:user1:data",
        "subject:user1:prefs",
        "other:key",
    ]
    c.storage.get.return_value = b"value"
    return c


def test_export_subject_returns_path():
    import tempfile
    c = _mock_container()
    path = export_subject("user1", c)
    assert path.startswith(os.path.join(tempfile.gettempdir(), "tasker-export-user1-"))
    assert path.endswith(".tar.gz")


def test_delete_subject_dry_run():
    c = _mock_container()
    res = delete_subject("user1", c, dry_run=True)
    assert res["dry_run"] is True
    assert "issue-1" in res["result"]["issues"]
    assert "subject:user1:data" in res["result"]["storage"]
    assert "subject:user1:prefs" in res["result"]["storage"]
    assert "issue-2" not in res["result"]["issues"]
    c.issue_repo.delete.assert_not_called()


def test_delete_subject_real():
    c = _mock_container()
    res = delete_subject("user1", c, dry_run=False)
    assert res["dry_run"] is False
    c.issue_repo.delete.assert_called_once_with("issue-1")
    c.storage.delete.assert_any_call("subject:user1:data")
    c.storage.delete.assert_any_call("subject:user1:prefs")


def test_delete_subject_no_issues():
    c = _mock_container()
    c.issue_repo.list_all.return_value = []
    res = delete_subject("nobody", c, dry_run=True)
    assert len(res["result"]["issues"]) == 0
    assert len(res["result"]["storage"]) == 0


def test_export_subject_no_storage_keys():
    import tempfile
    c = _mock_container()
    c.storage.list_keys.return_value = []
    path = export_subject("user1", c)
    assert path.startswith(os.path.join(tempfile.gettempdir(), "tasker-export-user1-"))
    assert path.endswith(".tar.gz")
