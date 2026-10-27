from unittest.mock import Mock

import pytest
import typer

from socialseed_tasker.application import wiring
from socialseed_tasker.cli.commands import agent_commands


def test_agent_list_fetches_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    response = Mock()
    response.json.return_value = {"data": []}
    request = Mock(return_value=response)

    monkeypatch.setattr(agent_commands, "_get_api_url", lambda: "http://example.test")
    monkeypatch.setattr(agent_commands.httpx, "get", request)

    agent_commands.agent_list()

    request.assert_called_once_with("http://example.test/api/v1/agents", timeout=10)


def test_agent_architect_exits_when_driver_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(wiring, "get_driver", lambda: None)

    with pytest.raises(typer.Exit):
        agent_commands.agent_architect(issue_id="issue-1")
