"""Unit tests for CLI argument parsing and error handling."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_container() -> MagicMock:
    container = MagicMock()
    container.application.generate_agent_context = MagicMock()
    container.application.calculate_impact = MagicMock(return_value=["a", "b"])
    container.application.create_issue = MagicMock()
    container.application.add_dependency = MagicMock()
    container.parser = MagicMock()
    return container


def test_create_issue_missing_args_returns_error(capsys):
    """Calling create-issue without --title should exit with code 2."""
    from socialseed_tasker.cli.main import main

    with (
        patch("socialseed_tasker.cli.main.build_default_container", return_value=_make_mock_container()),
        pytest.raises(SystemExit) as exc,
    ):
        main(["create-issue", "--id", "x"])
    assert exc.value.code == 2


def test_create_issue_success(capsys):
    """Calling create-issue with required args should succeed."""
    from socialseed_tasker.cli.main import main

    with patch("socialseed_tasker.cli.main.build_default_container", return_value=_make_mock_container()):
        main(["create-issue", "--id", "i1", "--title", "Test"])

    j = json.loads(capsys.readouterr().out)
    assert j["status"] == "ok"
    assert j["command"] == "create-issue"
    assert j["issue"]["id"] == "i1"


def test_parse_file_nonexistent_returns_error(capsys):
    """Parsing a nonexistent file should produce JSON error on stderr."""
    from socialseed_tasker.cli.main import main

    mock_container = _make_mock_container()
    mock_container.parser.parse_file.side_effect = FileNotFoundError("no such file")

    with (
        patch("socialseed_tasker.cli.main.build_default_container", return_value=mock_container),
        pytest.raises(SystemExit) as exc,
    ):
        main(["parse-file", "--path", "/no/such/file.py"])
    assert exc.value.code == 2

    j = json.loads(capsys.readouterr().err)
    assert j.get("status") == "error"
    assert j.get("command") == "parse-file"


def test_calculate_impact_success(capsys):
    """Calling calculate-impact should return JSON with impact_set."""
    from socialseed_tasker.cli.main import main

    with patch("socialseed_tasker.cli.main.build_default_container", return_value=_make_mock_container()):
        main(["calculate-impact", "--issue-id", "i1"])

    j = json.loads(capsys.readouterr().out)
    assert j["status"] == "ok"
    assert "i1" in j["issue_id"]
    assert "a" in j["impact_set"]
