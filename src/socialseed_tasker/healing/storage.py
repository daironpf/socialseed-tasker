"""Disk persistence for auto-healing pipeline runs and patch artifacts (issue #520).

Runs are stored as a single JSON document (atomic replace on write) so
executions survive API restarts. Patch artifacts and pre-fix file backups
live next to it under the same base directory.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class HealingStorage:
    """JSON file store for pipeline runs plus patch/backup file helpers."""

    def __init__(self, base_dir: str | os.PathLike[str]) -> None:
        self.base_dir = Path(base_dir)
        self.patches_dir = self.base_dir / "patches"
        self.backups_dir = self.base_dir / "backups"
        self.runs_file = self.base_dir / "runs.json"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.patches_dir.mkdir(parents=True, exist_ok=True)
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ runs

    def load_runs(self) -> list[dict[str, Any]]:
        if not self.runs_file.exists():
            return []
        try:
            data = json.loads(self.runs_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        return data if isinstance(data, list) else []

    def save_runs(self, runs: list[dict[str, Any]]) -> None:
        tmp_file = self.runs_file.with_suffix(".json.tmp")
        tmp_file.write_text(json.dumps(runs, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp_file, self.runs_file)

    # ---------------------------------------------------------------- patches

    def _patch_path(self, run_id: str, patch_id: str) -> Path:
        safe_run = "".join(c for c in run_id if c.isalnum() or c in "-_")
        safe_patch = "".join(c for c in patch_id if c.isalnum() or c in "-_")
        return self.patches_dir / f"{safe_run}_{safe_patch}.patch"

    def save_patch(self, run_id: str, patch_id: str, content: str) -> Path:
        path = self._patch_path(run_id, patch_id)
        path.write_text(content, encoding="utf-8")
        return path

    def read_patch(self, run_id: str, patch_id: str) -> str | None:
        path = self._patch_path(run_id, patch_id)
        if not path.exists():
            return None
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return None

    def delete_patch(self, run_id: str, patch_id: str) -> None:
        path = self._patch_path(run_id, patch_id)
        if path.exists():
            path.unlink()

    # ---------------------------------------------------------------- backups

    def save_backup(self, run_id: str, files: dict[str, str]) -> None:
        path = self.backups_dir / f"{run_id}.json"
        path.write_text(json.dumps(files, ensure_ascii=False), encoding="utf-8")

    def restore_backup(self, run_id: str, workspace: Path) -> list[str]:
        """Restore files saved before the fix stage. Returns restored paths."""
        path = self.backups_dir / f"{run_id}.json"
        if not path.exists():
            return []
        try:
            files = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        workspace_root = workspace.resolve()
        restored: list[str] = []
        for rel, content in files.items():
            target = (workspace / rel).resolve()
            if not str(target).startswith(str(workspace_root)):
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            restored.append(rel)
        return restored
