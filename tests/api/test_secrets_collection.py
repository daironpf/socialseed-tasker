from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.auth.rbac import RBAC
from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import secrets as secrets_module
from socialseed_tasker.secrets.core import SecretsStore

ADMIN_JWT = issue_tokens(
    {"id": "u-admin", "username": "u-admin", "role": "ADMIN", "permissions": ["admin"]}
)["access_token"]
READER_JWT = issue_tokens(
    {"id": "u-reader", "username": "u-reader", "role": "DEVELOPER", "permissions": ["read:context"]}
)["access_token"]


@pytest.fixture()
def client() -> TestClient:
    storage = MemoryStorage()
    container = SimpleNamespace(
        rbac=RBAC(),
        storage=storage,
        secrets_store=SecretsStore(storage),
    )
    app = create_app()
    app.dependency_overrides[secrets_module._get_container] = lambda: container
    with TestClient(app) as test_client:
        yield test_client


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_secret_collection_returns_metadata_without_values(client: TestClient) -> None:
    store = client.app.dependency_overrides[secrets_module._get_container]().secrets_store
    store.put_secret("database/password", b"never-return-this", {"owner": "platform"})
    store.put_secret("api/token", b"another-hidden-value", {"environment": "test"})

    response = client.get("/api/v1/secrets", headers=_headers(ADMIN_JWT))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["error"] is None
    assert [secret["name"] for secret in body["data"]] == [
        "api/token",
        "database/password",
    ]
    assert body["data"][1]["metadata"] == {"owner": "platform"}
    assert "value" not in body["data"][1]
    assert "never-return-this" not in response.text
    assert "another-hidden-value" not in response.text
    assert "audit" not in [secret["name"] for secret in body["data"]]


def test_secret_collection_requires_identity(client: TestClient) -> None:
    response = client.get("/api/v1/secrets")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_secret_collection_requires_admin_permission(client: TestClient) -> None:
    response = client.get("/api/v1/secrets", headers=_headers(READER_JWT))

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_secret_collection_supports_x_api_key_permission_guard(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "socialseed_tasker.auth.auth.load_auth_provider",
        lambda: SimpleNamespace(
            verify_token=lambda token: "u-admin" if token == "valid-key" else None,
            get_user_info=lambda user_id: {"permissions": ["admin"]},
        ),
    )
    response = client.get("/api/v1/secrets", headers={"X-API-Key": "valid-key"})

    assert response.status_code == 200, response.text
