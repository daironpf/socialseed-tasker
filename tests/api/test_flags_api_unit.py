from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app


@pytest.fixture
def mock_container():
    container = MagicMock()
    container.runtime_config = MagicMock()
    container.runtime_config.list.return_value = {"f1": "v1"}
    container.runtime_config.get.return_value = "v1"
    container.rbac = MagicMock()
    container.rbac.has_permission.return_value = True
    return container


@pytest.fixture
def mock_auth():
    with patch("socialseed_tasker.auth.auth.load_auth_provider") as m:
        provider = MagicMock()
        provider.verify_token.return_value = "admin-user"
        m.return_value = provider
        yield m


def test_api_list_flags(mock_container, mock_auth):
    with patch("socialseed_tasker.cli.wiring.build_default_container", return_value=mock_container):
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/v1/admin/flags", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["flags"] == {"f1": "v1"}


def test_api_get_flag_found(mock_container, mock_auth):
    with patch("socialseed_tasker.cli.wiring.build_default_container", return_value=mock_container):
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/v1/admin/flags/f1", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["name"] == "f1"
    assert data["value"] == "v1"


def test_api_get_flag_not_found(mock_container, mock_auth):
    mock_container.runtime_config.get.return_value = None
    with patch("socialseed_tasker.cli.wiring.build_default_container", return_value=mock_container):
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/v1/admin/flags/nonexistent", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 404


def test_api_set_flag(mock_container, mock_auth):
    with patch("socialseed_tasker.cli.wiring.build_default_container", return_value=mock_container):
        app = create_app()
        client = TestClient(app)
        resp = client.post(
            "/api/v1/admin/flags",
            json={"name": "new_flag", "value": "new_val"},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["name"] == "new_flag"
    assert data["value"] == "new_val"


def test_api_set_flag_missing_name(mock_container, mock_auth):
    with patch("socialseed_tasker.cli.wiring.build_default_container", return_value=mock_container):
        app = create_app()
        client = TestClient(app)
        resp = client.post(
            "/api/v1/admin/flags",
            json={"value": "x"},
            headers={"Authorization": "Bearer test-token"},
        )
    assert resp.status_code == 400


def test_api_delete_flag(mock_container, mock_auth):
    with patch("socialseed_tasker.cli.wiring.build_default_container", return_value=mock_container):
        app = create_app()
        client = TestClient(app)
        resp = client.delete("/api/v1/admin/flags/f1", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["name"] == "f1"


def test_api_unauthorized(mock_container, mock_auth):
    mock_auth.return_value.verify_token.return_value = None
    with patch("socialseed_tasker.cli.wiring.build_default_container", return_value=mock_container):
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/v1/admin/flags", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 403


def test_api_forbidden(mock_container, mock_auth):
    mock_container.rbac.has_permission.return_value = False
    with patch("socialseed_tasker.cli.wiring.build_default_container", return_value=mock_container):
        app = create_app()
        client = TestClient(app)
        resp = client.get("/api/v1/admin/flags", headers={"Authorization": "Bearer test-token"})
    assert resp.status_code == 403
