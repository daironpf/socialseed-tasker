"""Tests for local file storage utilities."""

import json
import tempfile
from pathlib import Path

import pytest

from socialseed_tasker.storage.local_files.file_store import (
    atomic_write,
    read_json,
    delete_file,
    backup_data,
    restore_data,
    list_backups,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


class TestAtomicWrite:
    def test_write_new_file(self, temp_dir):
        path = temp_dir / "test.json"
        data = {"key": "value"}
        atomic_write(path, data)
        assert path.exists()
        assert json.loads(path.read_text()) == data

    def test_overwrite_existing(self, temp_dir):
        path = temp_dir / "test.json"
        atomic_write(path, {"old": "data"})
        atomic_write(path, {"new": "data"})
        assert json.loads(path.read_text()) == {"new": "data"}

    def test_creates_parent_dirs(self, temp_dir):
        path = temp_dir / "nested" / "dir" / "test.json"
        atomic_write(path, {"test": True})
        assert path.exists()


class TestReadJson:
    def test_read_existing_file(self, temp_dir):
        path = temp_dir / "test.json"
        path.write_text('{"key": "value"}')
        assert read_json(path) == {"key": "value"}

    def test_read_missing_returns_none(self, temp_dir):
        path = temp_dir / "nonexistent.json"
        assert read_json(path) is None


class TestDeleteFile:
    def test_delete_existing(self, temp_dir):
        path = temp_dir / "test.txt"
        path.write_text("content")
        delete_file(path)
        assert not path.exists()

    def test_delete_missing_no_error(self, temp_dir):
        path = temp_dir / "nonexistent.txt"
        delete_file(path)


class TestBackupRestore:
    def test_backup_creates_directory(self, temp_dir):
        data_dir = temp_dir / "data"
        data_dir.mkdir()
        (data_dir / "test.txt").write_text("content")
        backup_dir = temp_dir / "backups"
        backup_path = backup_data(data_dir, backup_dir)
        assert backup_path.exists()
        assert (backup_path / "test.txt").read_text() == "content"

    def test_backup_empty_dir(self, temp_dir):
        data_dir = temp_dir / "empty"
        data_dir.mkdir()
        backup_dir = temp_dir / "backups"
        backup_path = backup_data(data_dir, backup_dir)
        assert backup_path.exists()

    def test_restore_overwrites(self, temp_dir):
        backup_dir = temp_dir / "backup"
        target_dir = temp_dir / "target"
        backup_dir.mkdir()
        (backup_dir / "restored.txt").write_text("content")
        restore_data(backup_dir, target_dir)
        assert (target_dir / "restored.txt").read_text() == "content"


class TestListBackups:
    def test_list_sorted_newest_first(self, temp_dir):
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir()
        (backup_dir / "tasker_backup_20240101_120000").touch()
        (backup_dir / "tasker_backup_20240102_120000").touch()
        backups = list_backups(backup_dir)
        assert len(backups) == 2
        assert backups[0].name == "tasker_backup_20240102_120000"

    def test_empty_dir_returns_empty_list(self, temp_dir):
        backup_dir = temp_dir / "backups"
        backup_dir.mkdir()
        assert list_backups(backup_dir) == []
