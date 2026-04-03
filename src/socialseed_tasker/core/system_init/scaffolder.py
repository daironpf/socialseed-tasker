"""Scaffolder service - orchestrates file system operations for project injection.

Intent: Provide a pure-domain service that copies template assets from
the library into an external project's tasker/ directory.
Business Value: Enables one-command setup of Tasker infrastructure in
any project without manual file management.
"""

from __future__ import annotations

import shutil
from collections.abc import Callable
from pathlib import Path

from socialseed_tasker.core.system_init.entities import (
    FileOperation,
    ScaffoldResult,
    ScaffoldStatus,
)


class ScaffolderService:
    """Copies template assets into a target project directory.

    Intent: Abstract file system operations behind a domain service
    so the scaffolding logic can be tested and extended independently.
    Business Value: Provides a reliable, repeatable setup process that
    works across different operating systems and project structures.
    """

    def __init__(
        self,
        template_dir: Path,
        progress_callback: Callable[[FileOperation], None] | None = None,
    ) -> None:
        """Initialize the scaffolder.

        Args:
            template_dir: Root directory containing template assets.
            progress_callback: Optional callback invoked for each file operation.
        """
        self._template_dir = template_dir
        self._progress_callback = progress_callback

    def scaffold(
        self,
        target_dir: Path,
        force: bool = False,
    ) -> ScaffoldResult:
        """Copy all template assets into the target directory.

        Creates the tasker/ directory structure and copies skills,
        configs, and docker-compose.yml from the bundled templates.

        Args:
            target_dir: Root of the external project (tasker/ will be created inside).
            force: If True, overwrite existing files. Otherwise skip them.

        Returns:
            ScaffoldResult with details of all file operations performed.
        """
        tasker_dir = target_dir / "tasker"
        result = ScaffoldResult(target_dir=tasker_dir)

        if not self._template_dir.exists():
            result.add_operation(
                FileOperation(
                    source=self._template_dir,
                    destination=tasker_dir,
                    status=ScaffoldStatus.ERROR,
                    error_message=f"Template directory not found: {self._template_dir}",
                )
            )
            return result

        tasker_dir.mkdir(parents=True, exist_ok=True)

        for template_path in self._template_dir.rglob("*"):
            if template_path.is_file():
                op = self._copy_template_file(template_path, tasker_dir, force)
                result.add_operation(op)
                if self._progress_callback:
                    self._progress_callback(op)

        return result

    def _copy_template_file(
        self,
        template_path: Path,
        tasker_dir: Path,
        force: bool,
    ) -> FileOperation:
        """Copy a single template file to the target structure.

        Preserves the relative directory structure from the template root.
        """
        relative_path = template_path.relative_to(self._template_dir)
        destination = tasker_dir / relative_path

        if destination.exists() and not force:
            return FileOperation(
                source=template_path,
                destination=destination,
                status=ScaffoldStatus.SKIPPED,
            )

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(template_path), str(destination))

            status = ScaffoldStatus.OVERWRITTEN if destination.exists() else ScaffoldStatus.CREATED
            if not force:
                status = ScaffoldStatus.CREATED

            return FileOperation(
                source=template_path,
                destination=destination,
                status=status,
            )
        except (OSError, shutil.Error) as exc:
            return FileOperation(
                source=template_path,
                destination=destination,
                status=ScaffoldStatus.ERROR,
                error_message=str(exc),
            )

    def list_available_templates(self) -> list[Path]:
        """Return all template files available for scaffolding."""
        if not self._template_dir.exists():
            return []
        return sorted(p for p in self._template_dir.rglob("*") if p.is_file())
