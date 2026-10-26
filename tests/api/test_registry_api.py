"""Registry API: envelope responses, semver validation and the DELETE routes.

Follow-up of the full-endpoint audit: ``GET|POST /api/v1/registry/*`` answered
plain dicts instead of the standard ``{data, error, meta}`` envelope, the
``version`` field was not pinned to semver in the request schema (the handler
replied 400 after the fact) and there was no way to remove a registered schema
or dataset through the API at all.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.data_catalog.registry import SchemaRegistry
from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.infrastructure.web_api.app import create_app


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    storage = MemoryStorage()
    registry = SchemaRegistry(storage)
    monkeypatch.setattr(
        "socialseed_tasker.data_catalog.api.build_default_container",
        lambda: SimpleNamespace(schema_registry=registry),
    )
    return TestClient(create_app())


def test_register_schema_returns_envelope(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/registry/schemas",
        json={"name": "order", "version": "1.0.0", "schema": {"type": "object"}},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["data"]["name"] == "order"
    assert body["data"]["version"] == "1.0.0"
    assert "meta" in body


def test_register_schema_rejects_non_semver_with_422(client: TestClient) -> None:
    resp = client.post(
        "/api/v1/registry/schemas",
        json={"name": "order", "version": "latest", "schema": {}},
    )
    assert resp.status_code == 422, resp.text
    assert "pattern" in resp.text or "semver" in resp.text.lower()


def test_list_versions_and_get_schema_envelope(client: TestClient) -> None:
    client.post(
        "/api/v1/registry/schemas",
        json={"name": "order", "version": "1.0.0", "schema": {"type": "object"}},
    )
    versions = client.get("/api/v1/registry/schemas/order/versions")
    assert versions.status_code == 200, versions.text
    assert versions.json()["data"]["versions"] == ["1.0.0"]

    single = client.get("/api/v1/registry/schemas/order/1.0.0")
    assert single.status_code == 200, single.text
    assert single.json()["data"]["schema"] == {"type": "object"}


def test_delete_schema_roundtrip_and_404(client: TestClient) -> None:
    client.post(
        "/api/v1/registry/schemas",
        json={"name": "order", "version": "1.0.0", "schema": {}},
    )
    client.post(
        "/api/v1/registry/schemas",
        json={"name": "order", "version": "1.0.1", "schema": {}},
    )
    resp = client.delete("/api/v1/registry/schemas/order")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["deleted"] is True

    after = client.get("/api/v1/registry/schemas/order/versions")
    assert after.json()["data"]["versions"] == []
    single = client.get("/api/v1/registry/schemas/order/1.0.0")
    assert single.status_code == 404

    missing = client.delete("/api/v1/registry/schemas/order")
    assert missing.status_code == 404, missing.text


def test_delete_dataset_roundtrip_and_404(client: TestClient) -> None:
    client.post(
        "/api/v1/registry/datasets",
        json={
            "dataset_id": "ds-1",
            "title": "Orders",
            "description": "d",
            "schema_name": "order",
            "default_schema_version": "1.0.0",
            "owner": "team",
        },
    )
    listed = client.get("/api/v1/registry/datasets")
    assert [d["dataset_id"] for d in listed.json()["data"]["datasets"]] == ["ds-1"]

    resp = client.delete("/api/v1/registry/datasets/ds-1")
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["deleted"] is True

    after = client.get("/api/v1/registry/datasets")
    assert after.json()["data"]["datasets"] == []
    missing = client.delete("/api/v1/registry/datasets/ds-1")
    assert missing.status_code == 404, missing.text
