from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from socialseed_tasker.application.actions import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    InvalidEntityError,
    RemoteServiceError,
)
from socialseed_tasker.infrastructure.http.api_client import ApiHttpClient


@pytest.fixture
def client():
    return ApiHttpClient(base_url="http://localhost:8888", api_key="test-key", timeout=5)


def test_health_check_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    client._client.get = MagicMock(return_value=mock_resp)
    assert client.health_check() is True


def test_health_check_failure(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    client._client.get = MagicMock(return_value=mock_resp)
    assert client.health_check() is False


def test_health_check_exception(client):
    client._client.get = MagicMock(side_effect=Exception("connection refused"))
    assert client.health_check() is False


def test_request_get_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"data": {"id": "123"}}'
    mock_resp.json.return_value = {"data": {"id": "123"}}
    client._client.request = MagicMock(return_value=mock_resp)

    result = client.request("GET", "/api/v1/components/123")
    assert result == {"id": "123"}


def test_request_get_list(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'[{"id": "1"}, {"id": "2"}]'
    mock_resp.json.return_value = [{"id": "1"}, {"id": "2"}]
    client._client.request = MagicMock(return_value=mock_resp)

    result = client.request("GET", "/api/v1/components")
    assert result == [{"id": "1"}, {"id": "2"}]


def test_request_404_returns_none(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = "Not Found"
    client._client.request = MagicMock(return_value=mock_resp)

    result = client.request("GET", "/api/v1/components/nonexistent")
    assert result is None


def test_request_400_raises_invalid_entity(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "Validation error"
    client._client.request = MagicMock(return_value=mock_resp)

    with pytest.raises(InvalidEntityError, match="Validation error"):
        client.request("POST", "/api/v1/components", json={})


def test_request_401_raises_authentication(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.text = "Unauthorized"
    client._client.request = MagicMock(return_value=mock_resp)

    with pytest.raises(AuthenticationError, match="Unauthorized"):
        client.request("GET", "/api/v1/issues")


def test_request_403_raises_authorization(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    mock_resp.text = "Forbidden"
    client._client.request = MagicMock(return_value=mock_resp)

    with pytest.raises(AuthorizationError, match="Forbidden"):
        client.request("DELETE", "/api/v1/issues/123")


def test_request_409_raises_conflict(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 409
    mock_resp.text = "Conflict"
    client._client.request = MagicMock(return_value=mock_resp)

    with pytest.raises(ConflictError, match="Conflict"):
        client.request("POST", "/api/v1/issues/123/dependencies", json={})


def test_request_500_raises_remote_service_error(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"
    client._client.request = MagicMock(return_value=mock_resp)

    with pytest.raises(RemoteServiceError, match="Server error"):
        client.request("GET", "/api/v1/issues")


def test_request_connection_error(client):
    client._client.request = MagicMock(side_effect=RemoteServiceError("Connection error"))

    with pytest.raises(RemoteServiceError):
        client.request("GET", "/api/v1/issues")


def test_paginate_single_page(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"items": [{"id": "1"}, {"id": "2"}], "page": 1, "next_page": false}'
    mock_resp.json.return_value = {"items": [{"id": "1"}, {"id": "2"}], "page": 1, "next_page": False}
    client._client.request = MagicMock(return_value=mock_resp)

    items = client.paginate("/api/v1/issues")
    assert len(items) == 2
    assert items[0]["id"] == "1"
    assert items[1]["id"] == "2"


def test_paginate_empty(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.content = b'{"items": [], "page": 1, "next_page": false}'
    mock_resp.json.return_value = {"items": [], "page": 1, "next_page": False}
    client._client.request = MagicMock(return_value=mock_resp)

    items = client.paginate("/api/v1/issues")
    assert items == []


def test_headers_include_api_key(client):
    headers = client._headers()
    assert headers["Authorization"] == "Bearer test-key"
    assert headers["Accept"] == "application/json"
    assert headers["Content-Type"] == "application/json"


def test_headers_no_api_key():
    client = ApiHttpClient(base_url="http://localhost:8888")
    headers = client._headers()
    assert "Authorization" not in headers


def test_context_manager():
    with ApiHttpClient(base_url="http://localhost:8888") as client:
        assert client is not None
        assert client.base_url == "http://localhost:8888"


def test_close(client):
    client._client.close = MagicMock()
    client.close()
    client._client.close.assert_called_once()
