"""Local file repository implementations.

JSON-based file storage implementing TaskRepositoryInterface for offline
and low-resource environments.
"""

from __future__ import annotations

import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
from socialseed_tasker.core.task_management.entities import (
    Component,
    Issue,
    IssueStatus,
)


class FileTaskRepository(TaskRepositoryInterface):
    """File-based implementation of TaskRepositoryInterface.

    Intent: Provide persistence without requiring Neo4j.
    Business Value: Enables offline operation, CI pipelines without databases,
    and serves as a testing backend.
    """

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._issues_dir = data_dir / "issues"
        self._components_dir = data_dir / "components"
        self._relationships_dir = data_dir / "relationships"
        self._issues_dir.mkdir(parents=True, exist_ok=True)
        self._components_dir.mkdir(parents=True, exist_ok=True)
        self._relationships_dir.mkdir(parents=True, exist_ok=True)

    # -- File I/O helpers -----------------------------------------------------

    def _issue_path(self, issue_id: str) -> Path:
        return self._issues_dir / f"{issue_id}.json"

    def _component_path(self, component_id: str) -> Path:
        return self._components_dir / f"{component_id}.json"

    def _relationship_path(self, source_id: str, target_id: str) -> Path:
        return self._relationships_dir / f"{source_id}_depends_on_{target_id}.json"

    def _read_json(self, path: Path) -> dict | None:
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _write_json(self, path: Path, data: dict) -> None:
        """Atomic write: write to temp file then rename."""
        dir_path = path.parent
        fd, tmp_path = tempfile.mkstemp(dir=str(dir_path), suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, default=str)
            os.replace(tmp_path, str(path))
        except Exception:
            os.unlink(tmp_path)
            raise

    def _delete_file(self, path: Path) -> None:
        if path.exists():
            path.unlink()

    # -- Issue CRUD ----------------------------------------------------------

    def create_issue(self, issue: Issue) -> None:
        self._write_json(self._issue_path(str(issue.id)), issue.model_dump(mode="json"))

    def get_issue(self, issue_id: str) -> Issue | None:
        data = self._read_json(self._issue_path(issue_id))
        if data is None:
            return None
        return Issue(**data)

    def update_issue(self, issue_id: str, updates: dict) -> Issue:
        path = self._issue_path(issue_id)
        data = self._read_json(path)
        if data is None:
            raise FileNotFoundError(f"Issue '{issue_id}' not found")
        data.update(updates)
        self._write_json(path, data)
        return Issue(**data)

    def close_issue(self, issue_id: str) -> Issue:
        from datetime import datetime, timezone

        return self.update_issue(
            issue_id,
            {
                "status": IssueStatus.CLOSED.value,
                "closed_at": datetime.now(timezone.utc).isoformat(),
            },
        )

    def delete_issue(self, issue_id: str) -> None:
        self._delete_file(self._issue_path(issue_id))
        # Remove related relationship files
        for f in self._relationships_dir.glob(f"{issue_id}_depends_on_*.json"):
            f.unlink()
        for f in self._relationships_dir.glob(f"*_depends_on_{issue_id}.json"):
            f.unlink()

    def list_issues(
        self,
        component_id: str | None = None,
        status: IssueStatus | None = None,
    ) -> list[Issue]:
        issues = []
        for path in self._issues_dir.glob("*.json"):
            data = self._read_json(path)
            if data is None:
                continue
            issue = Issue(**data)
            if component_id and str(issue.component_id) != component_id:
                continue
            if status and issue.status != status:
                continue
            issues.append(issue)
        return issues

    # -- Dependency management -----------------------------------------------

    def add_dependency(self, issue_id: str, depends_on_id: str) -> None:
        path = self._relationship_path(issue_id, depends_on_id)
        data = {
            "type": "DEPENDS_ON",
            "source_id": issue_id,
            "target_id": depends_on_id,
        }
        self._write_json(path, data)

    def remove_dependency(self, issue_id: str, depends_on_id: str) -> None:
        self._delete_file(self._relationship_path(issue_id, depends_on_id))

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        issues = []
        for path in self._relationships_dir.glob(f"{issue_id}_depends_on_*.json"):
            data = self._read_json(path)
            if data is None:
                continue
            dep_issue = self.get_issue(data["target_id"])
            if dep_issue is not None:
                issues.append(dep_issue)
        return issues

    def get_dependents(self, issue_id: str) -> list[Issue]:
        issues = []
        for path in self._relationships_dir.glob(f"*_depends_on_{issue_id}.json"):
            data = self._read_json(path)
            if data is None:
                continue
            dep_issue = self.get_issue(data["source_id"])
            if dep_issue is not None:
                issues.append(dep_issue)
        return issues

    def get_blocked_issues(self) -> list[Issue]:
        blocked: list[Issue] = []
        all_issues = self.list_issues()
        for issue in all_issues:
            if issue.status == IssueStatus.CLOSED:
                continue
            deps = self.get_dependencies(str(issue.id))
            if any(dep.status != IssueStatus.CLOSED for dep in deps):
                blocked.append(issue)
        return blocked

    # -- Component CRUD ------------------------------------------------------

    def create_component(self, component: Component) -> None:
        self._write_json(
            self._component_path(str(component.id)),
            component.model_dump(mode="json"),
        )

    def get_component(self, component_id: str) -> Component | None:
        data = self._read_json(self._component_path(component_id))
        if data is None:
            return None
        return Component(**data)

    def list_components(self, project: str | None = None) -> list[Component]:
        components = []
        for path in self._components_dir.glob("*.json"):
            data = self._read_json(path)
            if data is None:
                continue
            comp = Component(**data)
            if project and comp.project != project:
                continue
            components.append(comp)
        return components

    def update_component(self, component_id: str, updates: dict) -> Component:
        path = self._component_path(component_id)
        data = self._read_json(path)
        if data is None:
            raise FileNotFoundError(f"Component '{component_id}' not found")
        data.update(updates)
        self._write_json(path, data)
        return Component(**data)

    def delete_component(self, component_id: str) -> None:
        self._delete_file(self._component_path(component_id))

    # -- Transactions ----------------------------------------------------------

    @contextmanager
    def transaction(self):
        """Execute file operations atomically using a lock file."""
        import msvcrt

        lock_path = self._data_dir / ".tasker.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)

        lock_fd = None
        try:
            lock_fd = open(lock_path, "w")
            msvcrt.locking(lock_fd.fileno(), msvcrt.LK_LOCK, 1)
            yield
        finally:
            if lock_fd:
                try:
                    msvcrt.locking(lock_fd.fileno(), msvcrt.LK_UNLCK, 1)
                    lock_fd.close()
                except (OSError, IOError):
                    pass
