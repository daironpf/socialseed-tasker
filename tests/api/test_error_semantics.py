from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.delenv("TASKER_API_KEY", raising=False)
    monkeypatch.delenv("TASKER_AUTH_ENABLED", raising=False)
    app = create_app()

    @app.get("/api/v1/test-http-error/{status_code}")
    async def http_error(status_code: int) -> None:
        raise HTTPException(status_code=status_code, detail="controlled error")

    @app.get("/api/v1/test-value-error")
    async def value_error() -> None:
        raise ValueError("badly formed hexadecimal UUID string")

    return TestClient(app)


@pytest.mark.parametrize(
    ("status_code", "error_code"),
    [
        (400, "VALIDATION_ERROR"),
        (401, "UNAUTHORIZED"),
        (403, "FORBIDDEN"),
        (404, "NOT_FOUND"),
        (405, "METHOD_NOT_ALLOWED"),
        (409, "CONFLICT"),
        (422, "INVALID_PATH_PARAM"),
        (503, "SERVICE_UNAVAILABLE"),
    ],
)
def test_http_exceptions_use_error_envelope(
    client: TestClient, status_code: int, error_code: str
) -> None:
    response = client.get(f"/api/v1/test-http-error/{status_code}")

    assert response.status_code == status_code
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == error_code
    assert body["error"]["message"] == "controlled error"
    assert body["meta"]["timestamp"]
    assert body["meta"]["request_id"]


def test_value_error_does_not_expose_parser_message(client: TestClient) -> None:
    response = client.get("/api/v1/test-value-error")

    assert response.status_code == 400
    body = response.json()
    assert body["data"] is None
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["message"] == "Invalid value for request"
    assert "hexadecimal" not in response.text
    assert body["meta"]["request_id"]
