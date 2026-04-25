"""Tests for the ScaffolderService system initialization."""

import tempfile
from pathlib import Path

import pytest

from socialseed_tasker.core.system_init.entities import (
    FileOperation,
    ScaffoldResult,
    ScaffoldStatus,
)
from socialseed_tasker.core.system_init.scaffolder import ScaffolderService


@pytest.fixture()
def template_dir() -> Path:
    """Create a temporary template structure for testing."""
    tmp = Path(tempfile.mkdtemp())
    skills_dir = tmp / "skills"
    configs_dir = tmp / "configs"
    skills_dir.mkdir()
    configs_dir.mkdir()

    (skills_dir / "test_skill.py").write_text("# test skill\n")
    (configs_dir / ".env.example").write_text("KEY=value\n")
    (tmp / "docker-compose.yml").write_text("services:\n")

    return tmp


@pytest.fixture()
def target_dir() -> Path:
    """Create a temporary target project directory."""
    return Path(tempfile.mkdtemp())


class TestScaffoldResult:
    def test_empty_result_is_success(self) -> None:
        result = ScaffoldResult(target_dir=Path("/tmp"))
        assert result.success is True
        assert result.created_count == 0
        assert result.overwritten_count == 0
        assert result.skipped_count == 0
        assert result.error_count == 0

    def test_created_count(self) -> None:
        result = ScaffoldResult(target_dir=Path("/tmp"))
        result.add_operation(
            FileOperation(
                source=Path("a"),
                destination=Path("b"),
                status=ScaffoldStatus.CREATED,
            )
        )
        result.add_operation(
            FileOperation(
                source=Path("c"),
                destination=Path("d"),
                status=ScaffoldStatus.CREATED,
            )
        )
        assert result.created_count == 2
        assert result.success is True

    def test_overwritten_count(self) -> None:
        result = ScaffoldResult(target_dir=Path("/tmp"))
        result.add_operation(
            FileOperation(
                source=Path("a"),
                destination=Path("b"),
                status=ScaffoldStatus.OVERWRITTEN,
            )
        )
        assert result.overwritten_count == 1

    def test_skipped_count(self) -> None:
        result = ScaffoldResult(target_dir=Path("/tmp"))
        result.add_operation(
            FileOperation(
                source=Path("a"),
                destination=Path("b"),
                status=ScaffoldStatus.SKIPPED,
            )
        )
        assert result.skipped_count == 1

    def test_error_marks_failure(self) -> None:
        result = ScaffoldResult(target_dir=Path("/tmp"))
        result.add_operation(
            FileOperation(
                source=Path("a"),
                destination=Path("b"),
                status=ScaffoldStatus.ERROR,
                error_message="Permission denied",
            )
        )
        assert result.success is False
        assert result.error_count == 1


class TestScaffolderService:
    def test_scaffold_creates_structure(self, template_dir: Path, target_dir: Path) -> None:
        service = ScaffolderService(template_dir)
        result = service.scaffold(target_dir)

        assert result.success is True
        assert result.created_count > 0
        assert result.error_count == 0

        tasker_dir = target_dir / "tasker"
        assert tasker_dir.exists()
        assert (tasker_dir / "skills" / "test_skill.py").exists()
        assert (tasker_dir / "configs" / ".env.example").exists()
        assert (tasker_dir / "docker-compose.yml").exists()

    def test_scaffold_skips_existing_without_force(self, template_dir: Path, target_dir: Path) -> None:
        service = ScaffolderService(template_dir)

        # First scaffold
        result1 = service.scaffold(target_dir)
        assert result1.created_count > 0

        # Second scaffold without force
        result2 = service.scaffold(target_dir)
        assert result2.skipped_count > 0
        assert result2.created_count == 0

    def test_scaffold_overwrites_with_force(self, template_dir: Path, target_dir: Path) -> None:
        service = ScaffolderService(template_dir)

        # First scaffold
        service.scaffold(target_dir)

        # Second scaffold with force
        result = service.scaffold(target_dir, force=True)
        assert result.overwritten_count > 0

    def test_scaffold_missing_template_dir(self, target_dir: Path) -> None:
        service = ScaffolderService(Path("/nonexistent/templates"))
        result = service.scaffold(target_dir)

        assert result.success is False
        assert result.error_count > 0

    def test_list_available_templates(self, template_dir: Path) -> None:
        service = ScaffolderService(template_dir)
        templates = service.list_available_templates()

        assert len(templates) == 3
        assert any("test_skill.py" in str(t) for t in templates)
        assert any("docker-compose.yml" in str(t) for t in templates)

    def test_list_available_templates_empty(self) -> None:
        service = ScaffolderService(Path("/nonexistent"))
        assert service.list_available_templates() == []

    def test_progress_callback(self, template_dir: Path, target_dir: Path) -> None:
        operations: list[FileOperation] = []

        def callback(op: FileOperation) -> None:
            operations.append(op)

        service = ScaffolderService(template_dir, progress_callback=callback)
        service.scaffold(target_dir)

        assert len(operations) > 0
        assert all(op.status == ScaffoldStatus.CREATED for op in operations)

    def test_scaffold_creates_project_readme(self, template_dir: Path, target_dir: Path) -> None:
        """Test that project_readme.md is copied to project root as README.md."""
        project_readme = template_dir / "project_readme.md"
        project_readme.write_text("# Project Documentation\nQuick start guide.")

        service = ScaffolderService(template_dir)
        result = service.scaffold(target_dir)

        assert result.success is True
        readme_path = target_dir / "README.md"
        assert readme_path.exists()
        assert "Project Documentation" in readme_path.read_text()

    def test_project_readme_skipped_without_force(self, template_dir: Path, target_dir: Path) -> None:
        """Test that existing README.md is skipped without force."""
        project_readme = template_dir / "project_readme.md"
        project_readme.write_text("# New Content\n")

        target_readme = target_dir / "README.md"
        target_readme.write_text("# Existing Content\n")

        service = ScaffolderService(template_dir)
        result = service.scaffold(target_dir)

        assert result.success is True
        assert target_readme.read_text() == "# Existing Content\n"

    def test_project_readme_overwritten_with_force(self, template_dir: Path, target_dir: Path) -> None:
        """Test that README.md is overwritten when force=True."""
        project_readme = template_dir / "project_readme.md"
        project_readme.write_text("# New Content\n")

        target_readme = target_dir / "README.md"
        target_readme.write_text("# Existing Content\n")

        service = ScaffolderService(template_dir)
        result = service.scaffold(target_dir, force=True)

        assert result.success is True
        assert target_readme.read_text() == "# New Content\n"

    def test_scaffold_copies_frontend_build(self, template_dir: Path, target_dir: Path) -> None:
        """Test that frontend/dist/ is copied to tasker/frontend/ when it exists."""
        frontend_dist = target_dir / "frontend" / "dist"
        frontend_dist.mkdir(parents=True)
        (frontend_dist / "index.html").write_text("<html>Built App</html>")
        assets_dir = frontend_dist / "assets"
        assets_dir.mkdir()
        (assets_dir / "app.js").write_text("// compiled code")

        service = ScaffolderService(template_dir)
        result = service.scaffold(target_dir)

        assert result.success is True
        tasker_frontend = target_dir / "tasker" / "frontend"
        assert (tasker_frontend / "index.html").exists()
        assert (tasker_frontend / "assets" / "app.js").exists()
        assert (tasker_frontend / "index.html").read_text() == "<html>Built App</html>"

    def test_scaffold_skips_frontend_copy_without_force(
        self, template_dir: Path, target_dir: Path
    ) -> None:
        """Test that existing tasker/frontend/ files are skipped without force."""
        frontend_dist = target_dir / "frontend" / "dist"
        frontend_dist.mkdir(parents=True)
        (frontend_dist / "index.html").write_text("<html>New Build</html>")

        tasker_frontend = target_dir / "tasker" / "frontend"
        tasker_frontend.mkdir(parents=True)
        (tasker_frontend / "index.html").write_text("<html>Old Build</html>")

        service = ScaffolderService(template_dir)
        result = service.scaffold(target_dir)

        assert result.success is True
        assert (tasker_frontend / "index.html").read_text() == "<html>Old Build</html>"

    def test_scaffold_overwrites_frontend_with_force(
        self, template_dir: Path, target_dir: Path
    ) -> None:
        """Test that tasker/frontend/ is overwritten when force=True."""
        frontend_dist = target_dir / "frontend" / "dist"
        frontend_dist.mkdir(parents=True)
        (frontend_dist / "index.html").write_text("<html>New Build</html>")

        tasker_frontend = target_dir / "tasker" / "frontend"
        tasker_frontend.mkdir(parents=True)
        (tasker_frontend / "index.html").write_text("<html>Old Build</html>")

        service = ScaffolderService(template_dir)
        result = service.scaffold(target_dir, force=True)

        assert result.success is True
        assert (tasker_frontend / "index.html").read_text() == "<html>New Build</html>"
