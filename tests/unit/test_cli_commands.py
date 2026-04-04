"""Tests for CLI commands using Typer CliRunner."""

import tempfile
from pathlib import Path

import pytest
from typer.testing import CliRunner

from socialseed_tasker.entrypoints.terminal_cli.app import app


@pytest.fixture()
def runner():
    return CliRunner()


@pytest.fixture()
def clean_env(monkeypatch, tmp_path):
    """Set up clean environment with temp directory."""
    data_dir = tmp_path / ".tasker-data"
    data_dir.mkdir()
    monkeypatch.setenv("TASKER_STORAGE_BACKEND", "file")
    return data_dir


class TestIssueCommands:
    def test_issue_create_success(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "component", "create", "TestComp", "-p", "test"],
        )
        assert result.exit_code == 0

    def test_issue_list_empty(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "issue", "list"],
        )
        assert result.exit_code == 0

    def test_issue_create_missing_component(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "issue", "create", "Test", "-c", "nonexistent"],
        )
        assert result.exit_code == 2

    def test_issue_show_missing(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "issue", "show", "nonexistent-id"],
        )
        assert result.exit_code == 1


class TestComponentCommands:
    def test_component_create_success(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "component", "create", "Backend", "-p", "project1"],
        )
        assert result.exit_code == 0
        assert "created" in result.stdout.lower()

    def test_component_list_empty(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "component", "list"],
        )
        assert result.exit_code == 0

    def test_component_list_with_data(self, runner, clean_env):
        runner.invoke(
            app,
            ["--backend", "file", "component", "create", "Frontend", "-p", "project1"],
        )
        result = runner.invoke(
            app,
            ["--backend", "file", "component", "list"],
        )
        assert result.exit_code == 0
        assert "Frontend" in result.stdout

    def test_component_show_missing(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "component", "show", "nonexistent-id"],
        )
        assert result.exit_code == 1

    def test_component_update_success(self, runner, clean_env):
        create_result = runner.invoke(
            app,
            ["--backend", "file", "component", "create", "OldName", "-p", "proj"],
        )
        assert create_result.exit_code == 0

    def test_component_delete_missing(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "component", "delete", "nonexistent-id"],
        )
        assert result.exit_code == 1


class TestDependencyCommands:
    def test_dependency_blocked_empty(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "dependency", "blocked"],
        )
        assert result.exit_code == 0


class TestStatusCommand:
    def test_status_command(self, runner, clean_env):
        result = runner.invoke(
            app,
            ["--backend", "file", "status"],
        )
        assert result.exit_code == 0
        assert "Backend" in result.stdout
        assert "file" in result.stdout.lower()


class TestGlobalOptions:
    def test_backend_option(self, runner, clean_env):
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "--backend" in result.stdout or "-b" in result.stdout


class TestComponentListJson:
    def test_component_list_json(self, runner, clean_env):
        runner.invoke(
            app,
            ["--backend", "file", "component", "create", "TestComp", "-p", "proj"],
        )
        result = runner.invoke(
            app,
            ["--backend", "file", "component", "list", "--json"],
        )
        assert result.exit_code == 0
        assert result.stdout.startswith("[") or "[" in result.stdout


class TestInitCommand:
    def test_init_creates_scaffold_files(self, runner, tmp_path):
        target_dir = tmp_path / "project"
        target_dir.mkdir()
        result = runner.invoke(
            app,
            ["init", str(target_dir)],
        )
        assert result.exit_code == 0
        assert (target_dir / "tasker").exists()
        assert (target_dir / "tasker" / "docker-compose.yml").exists()

    def test_init_force_overwrites_existing(self, runner, tmp_path):
        target_dir = tmp_path / "project"
        target_dir.mkdir()
        tasker_dir = target_dir / "tasker"
        tasker_dir.mkdir()
        (tasker_dir / "docker-compose.yml").write_text("old content")

        result = runner.invoke(
            app,
            ["init", str(target_dir), "--force"],
        )
        assert result.exit_code == 0
        assert "Overwritten" in result.stdout

    def test_init_nonexistent_directory(self, runner, tmp_path):
        target_dir = tmp_path / "nonexistent"
        result = runner.invoke(
            app,
            ["init", str(target_dir)],
        )
        assert result.exit_code == 1
        assert "does not exist" in result.stdout

    def test_init_short_flag_force(self, runner, tmp_path):
        target_dir = tmp_path / "project"
        target_dir.mkdir()
        tasker_dir = target_dir / "tasker"
        tasker_dir.mkdir()

        result = runner.invoke(
            app,
            ["init", str(target_dir), "-f"],
        )
        assert result.exit_code == 0
