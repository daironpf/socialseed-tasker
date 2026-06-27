from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("TASKER_INTEGRATION") != "1",
    reason="requires TASKER_INTEGRATION=1",
)


@pytest.fixture
def mock_container():
    container = MagicMock()
    container.runtime_config = MagicMock()
    container.runtime_config.list.return_value = {"flag_a": "value_a"}
    container.runtime_config.get.return_value = "value_a"
    container.rbac = MagicMock()
    container.rbac.has_permission.return_value = True
    return container


@pytest.fixture
def mock_auth():
    with patch("socialseed_tasker.auth.auth.load_auth_provider") as m:
        provider = MagicMock()
        provider.verify_token.return_value = "integration-user"
        m.return_value = provider
        yield m


def test_flag_roundtrip_via_cli_and_api(mock_container, mock_auth):
    """Verify that setting a flag via the CLI and reading via the API works."""
    from socialseed_tasker.cli.main import main

    with patch("socialseed_tasker.cli.main.build_default_container", return_value=mock_container):
        main(["flag-set", "--name", "integration_flag", "--value", "works", "--token", "fake-token"])
    mock_container.runtime_config.set.assert_called_with("integration_flag", "works")

    with patch("socialseed_tasker.cli.wiring.build_default_container", return_value=mock_container):
        from fastapi.testclient import TestClient
        from socialseed_tasker.infrastructure.web_api.app import create_app
        app = create_app()
        client = TestClient(app)
        resp = client.get(
            "/api/v1/admin/flags/integration_flag",
            headers={"Authorization": "Bearer fake-token"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "integration_flag"
        assert data["value"] == "value_a"
