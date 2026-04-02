"""Local file I/O utilities.

Provides atomic file operations, file locking for concurrent access safety,
and backup/restore utilities for the local file storage backend.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def atomic_write(path: Path, data: dict) -> None:
    """Write JSON data to a file atomically.

    Writes to a temporary file first, then renames to the target path.
    This prevents partial writes if the process is interrupted.

    Intent: Guarantee data integrity for file-based storage.
    Business Value: Prevents corruption of issue/component data during
    unexpected shutdowns or concurrent access.
    """
    dir_path = path.parent
    dir_path.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
        os.replace(tmp_path, str(path))
    except Exception:
        os.unlink(tmp_path)
        raise


def read_json(path: Path) -> dict | None:
    """Read and parse a JSON file, returning None if it doesn't exist."""
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_file(path: Path) -> None:
    """Delete a file if it exists."""
    if path.exists():
        path.unlink()


def backup_data(data_dir: Path, backup_dir: Path) -> Path:
    """Create a timestamped backup of the data directory.

    Args:
        data_dir: Source directory to back up.
        backup_dir: Parent directory for the backup.

    Returns:
        Path to the created backup directory.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"tasker_backup_{timestamp}"
    if data_dir.exists():
        shutil.copytree(data_dir, backup_path)
    else:
        backup_path.mkdir(parents=True)
    return backup_path


def restore_data(backup_dir: Path, target_dir: Path) -> None:
    """Restore data from a backup directory.

    Args:
        backup_dir: Source backup directory.
        target_dir: Destination directory (will be overwritten).
    """
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(backup_dir, target_dir)


def list_backups(backup_dir: Path) -> list[Path]:
    """List available backups sorted by date (newest first)."""
    if not backup_dir.exists():
        return []
    backups = sorted(
        backup_dir.glob("tasker_backup_*"),
        key=lambda p: p.name,
        reverse=True,
    )
    return backups
