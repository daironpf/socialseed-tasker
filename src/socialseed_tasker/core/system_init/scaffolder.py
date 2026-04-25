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
        output_dir: Path | None = None,
    ) -> ScaffoldResult:
        """Copy all template assets into the target directory.

        Creates the tasker/ directory structure and copies skills,
        configs, and docker-compose.yml from the bundled templates.
        Also copies project_readme.md to the project root as README.md.
        If frontend/dist/ exists in the project root, copies it to
        tasker/frontend/ for a working Kanban board.

        Args:
            target_dir: Root of the external project (tasker/ will be created inside).
            force: If True, overwrite existing files. Otherwise skip them.
            output_dir: Custom output directory. If None, creates tasker/ inside target_dir.

        Returns:
            ScaffoldResult with details of all file operations performed.
        """
        if output_dir:
            tasker_dir = output_dir
        else:
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

        self._copy_project_readme(target_dir, force, result)

        self._copy_frontend_build(target_dir, force, result)

        return result

    def _copy_project_readme(
        self,
        target_dir: Path,
        force: bool,
        result: ScaffoldResult,
    ) -> None:
        """Copy project_readme.md template to project root as README.md."""
        project_readme_template = self._template_dir / "project_readme.md"
        if not project_readme_template.exists():
            return

        readme_destination = target_dir / "README.md"

        if readme_destination.exists() and not force:
            result.add_operation(
                FileOperation(
                    source=project_readme_template,
                    destination=readme_destination,
                    status=ScaffoldStatus.SKIPPED,
                )
            )
            if self._progress_callback:
                self._progress_callback(
                    FileOperation(
                        source=project_readme_template,
                        destination=readme_destination,
                        status=ScaffoldStatus.SKIPPED,
                    )
                )
            return

        try:
            shutil.copy2(str(project_readme_template), str(readme_destination))
            status = ScaffoldStatus.OVERWRITTEN if readme_destination.exists() else ScaffoldStatus.CREATED
            op = FileOperation(
                source=project_readme_template,
                destination=readme_destination,
                status=status,
            )
            result.add_operation(op)
            if self._progress_callback:
                self._progress_callback(op)
        except (OSError, shutil.Error) as exc:
            op = FileOperation(
                source=project_readme_template,
                destination=readme_destination,
                status=ScaffoldStatus.ERROR,
                error_message=str(exc),
            )
            result.add_operation(op)
            if self._progress_callback:
                self._progress_callback(op)

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

    def _copy_frontend_build(
        self,
        target_dir: Path,
        force: bool,
        result: ScaffoldResult,
    ) -> None:
        """Copy frontend/dist/ build to tasker/frontend/ if it exists.

        This ensures users get a working Vue Kanban board immediately
        after scaffolding, instead of just placeholder HTML files.
        """
        frontend_dist = target_dir / "frontend" / "dist"
        if not frontend_dist.exists():
            return

        tasker_frontend = target_dir / "tasker" / "frontend"
        tasker_frontend.mkdir(parents=True, exist_ok=True)

        for src_path in frontend_dist.rglob("*"):
            if src_path.is_file():
                relative = src_path.relative_to(frontend_dist)
                dest_path = tasker_frontend / relative

                if dest_path.exists() and not force:
                    result.add_operation(
                        FileOperation(
                            source=src_path,
                            destination=dest_path,
                            status=ScaffoldStatus.SKIPPED,
                        )
                    )
                    continue

                try:
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(src_path), str(dest_path))
                    status = ScaffoldStatus.OVERWRITTEN if dest_path.exists() else ScaffoldStatus.CREATED
                    op = FileOperation(
                        source=src_path,
                        destination=dest_path,
                        status=status,
                    )
                    result.add_operation(op)
                    if self._progress_callback:
                        self._progress_callback(op)
                except (OSError, shutil.Error) as exc:
                    op = FileOperation(
                        source=src_path,
                        destination=dest_path,
                        status=ScaffoldStatus.ERROR,
                        error_message=str(exc),
                    )
                    result.add_operation(op)
                    if self._progress_callback:
                        self._progress_callback(op)
