"""Unit tests for the 'tasker setup' command (issue #542)."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import typer
from rich.console import Console

import socialseed_tasker.cli.setup_command as setup_cmd


@pytest.fixture
def out(monkeypatch):
    """Capture the module-level Rich console output."""
    buffer = io.StringIO()
    monkeypatch.setattr(
        setup_cmd,
        "console",
        Console(file=buffer, force_terminal=False, width=120, soft_wrap=True),
    )
    return buffer


def _fake_run_factory(calls, up_returncode=0, volume_stdout=""):
    def fake_run(command, **kwargs):
        calls.append({"command": list(command), **kwargs})
        result = MagicMock()
        result.stdout = ""
        result.stderr = ""
        result.returncode = 0
        if list(command)[:3] == ["docker", "volume", "ls"]:
            result.stdout = volume_stdout
        elif list(command)[:3] == ["docker", "compose", "up"]:
            result.returncode = up_returncode
            result.stderr = "boom" if up_returncode else ""
        elif list(command)[:3] == ["docker", "compose", "version"]:
            result.returncode = kwargs.get("version_rc", 0)
        return result

    return fake_run


def test_find_compose_file_walks_up(tmp_path):
    compose = tmp_path / "docker-compose.yml"
    compose.write_text("services: {}\n", encoding="utf-8")
    nested = tmp_path / "src" / "deep"
    nested.mkdir(parents=True)
    assert setup_cmd.find_compose_file(nested) == compose


def test_find_compose_file_not_found(tmp_path):
    assert setup_cmd.find_compose_file(tmp_path) is None


def test_check_docker_missing_binary(out):
    with patch("socialseed_tasker.cli.setup_command.shutil.which", return_value=None):
        with pytest.raises(typer.Exit) as exc:
            setup_cmd.check_docker()
    assert exc.value.exit_code == 1
    assert "Docker was not found" in out.getvalue()


def test_check_docker_missing_compose_plugin(out):
    run_result = MagicMock(returncode=1, stdout="", stderr="")
    with patch("socialseed_tasker.cli.setup_command.shutil.which", return_value="C:/docker.exe"):
        with patch("socialseed_tasker.cli.setup_command.subprocess.run", return_value=run_result):
            with pytest.raises(typer.Exit) as exc:
                setup_cmd.check_docker()
    assert exc.value.exit_code == 1
    assert "Docker Compose is not available" in out.getvalue()


def test_ensure_env_file_creates_defaults(tmp_path, monkeypatch, out):
    monkeypatch.setattr(setup_cmd, "neo4j_volume_exists", lambda: False)
    env_path = setup_cmd.ensure_env_file(tmp_path, 19001)
    assert env_path == tmp_path / ".env"
    text = env_path.read_text(encoding="utf-8")
    assert "TASKER_INSTALLED=false" in text
    assert "FRONTEND_PORT=19001" in text
    assert "API_PORT=8888" in text
    assert "TASKER_NEO4J_PASSWORD=" in text
    password = setup_cmd.read_env_value(env_path, "TASKER_NEO4J_PASSWORD")
    assert password is not None
    assert password != setup_cmd.DEFAULT_NEO4J_PASSWORD
    assert len(password) >= 16
    assert "\r" not in text
    assert "Created .env" in out.getvalue()


def test_ensure_env_file_existing_volume_keeps_default_password(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_cmd, "neo4j_volume_exists", lambda: True)
    env_path = setup_cmd.ensure_env_file(tmp_path, 19001)
    assert setup_cmd.read_env_value(env_path, "TASKER_NEO4J_PASSWORD") == "neoSocial"


def test_ensure_env_file_preserves_existing(tmp_path):
    existing = tmp_path / ".env"
    existing.write_text("FRONTEND_PORT=9999\nTASKER_MODE=direct\n", encoding="utf-8")
    env_path = setup_cmd.ensure_env_file(tmp_path, 19001)
    assert env_path == existing
    assert existing.read_text(encoding="utf-8") == "FRONTEND_PORT=9999\nTASKER_MODE=direct\n"


def test_effective_frontend_port_prefers_existing_env(tmp_path, out):
    env_path = tmp_path / ".env"
    env_path.write_text("FRONTEND_PORT=9999\n", encoding="utf-8")
    assert setup_cmd.effective_frontend_port(env_path, 19001) == 9999
    assert "FRONTEND_PORT=9999" in out.getvalue()


def test_effective_frontend_port_uses_flag_when_absent(tmp_path):
    env_path = tmp_path / ".env"
    env_path.write_text("TASKER_MODE=direct\n", encoding="utf-8")
    assert setup_cmd.effective_frontend_port(env_path, 19001) == 19001


def test_setup_happy_path(tmp_path, monkeypatch, out):
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    calls = []
    fake_run = _fake_run_factory(calls)
    with patch("socialseed_tasker.cli.setup_command.shutil.which", return_value="C:/docker.exe"):
        with patch("socialseed_tasker.cli.setup_command.subprocess.run", side_effect=fake_run):
            with patch.object(setup_cmd, "neo4j_volume_exists", return_value=False):
                setup_cmd.setup_command(port=19001, dev=False)
    env_file = tmp_path / ".env"
    assert env_file.is_file()
    up = [c for c in calls if c["command"][:3] == ["docker", "compose", "up"]]
    assert len(up) == 1
    assert up[0]["command"] == ["docker", "compose", "up", "-d"]
    assert up[0]["cwd"] == str(tmp_path)
    assert up[0]["env"]["FRONTEND_PORT"] == "19001"
    assert "http://localhost:19001/setup" in out.getvalue()
    assert "Tasker services started" in out.getvalue()


def test_setup_dev_rebuilds_images(tmp_path, monkeypatch):
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    calls = []
    fake_run = _fake_run_factory(calls)
    with patch("socialseed_tasker.cli.setup_command.shutil.which", return_value="C:/docker.exe"):
        with patch("socialseed_tasker.cli.setup_command.subprocess.run", side_effect=fake_run):
            with patch.object(setup_cmd, "neo4j_volume_exists", return_value=False):
                setup_cmd.setup_command(port=19001, dev=True)
    up = [c for c in calls if c["command"][:3] == ["docker", "compose", "up"]]
    assert up[0]["command"] == ["docker", "compose", "up", "-d", "--build"]


def test_setup_missing_compose_file(tmp_path, monkeypatch, out):
    empty = tmp_path / "empty"
    empty.mkdir()
    monkeypatch.chdir(empty)
    with patch("socialseed_tasker.cli.setup_command.shutil.which", return_value="C:/docker.exe"):
        with patch("socialseed_tasker.cli.setup_command.subprocess.run", return_value=MagicMock(returncode=0)):
            with pytest.raises(typer.Exit) as exc:
                setup_cmd.setup_command(port=19001, dev=False)
    assert exc.value.exit_code == 1
    assert "docker-compose.yml not found" in out.getvalue()
    assert not (empty / ".env").exists()


def test_setup_compose_failure_exits(tmp_path, monkeypatch, out):
    (tmp_path / "docker-compose.yml").write_text("services: {}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    calls = []
    fake_run = _fake_run_factory(calls, up_returncode=1)
    with patch("socialseed_tasker.cli.setup_command.shutil.which", return_value="C:/docker.exe"):
        with patch("socialseed_tasker.cli.setup_command.subprocess.run", side_effect=fake_run):
            with patch.object(setup_cmd, "neo4j_volume_exists", return_value=False):
                with pytest.raises(typer.Exit) as exc:
                    setup_cmd.setup_command(port=19001, dev=False)
    assert exc.value.exit_code == 1
    assert "docker compose up failed" in out.getvalue()
    assert "http://localhost" not in out.getvalue()
