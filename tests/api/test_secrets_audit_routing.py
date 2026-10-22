"""Issue #581: ``GET /secrets/audit`` was shadowed by ``GET /secrets/{name}``.

The literal audit route was declared after the path-param template, so FastAPI
matched ``audit`` as a secret name and routed into ``api_get_secret_meta``,
which fed the JSON **array** stored under ``secrets:audit`` to
``entry.get(...)`` → ``AttributeError: 'list' object has no attribute 'get'``
→ 500. These tests pin: the literal route wins (200 + list), real secret names
still resolve to the metadata handler, and a non-dict storage entry yields a
typed 404 instead of a 500.
"""

from __future__ import annotations

import base64
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import secrets as secrets_module
from socialseed_tasker.secrets.core import SecretsStore


@pytest.fixture()
def client_and_store() -> tuple[TestClient, SecretsStore, MemoryStorage]:
    storage = MemoryStorage()
    store = SecretsStore(storage=storage)
    container = SimpleNamespace(storage=storage, secrets_store=store)
    app = create_app()
    app.dependency_overrides[secrets_module._get_container] = lambda: container
    return TestClient(app), store, storage


def test_secrets_audit_reaches_audit_handler_not_shadow(
    client_and_store: tuple[TestClient, SecretsStore, MemoryStorage],
) -> None:
    client, _store, _storage = client_and_store
    resp = client.get("/api/v1/secrets/audit")
    assert resp.status_code == 200, resp.text[:300]
    body = resp.json()
    assert body["status"] == "ok"
    assert body["audit"] == []


def test_secrets_audit_lists_events_after_put(
    client_and_store: tuple[TestClient, SecretsStore, MemoryStorage],
) -> None:
    client, _store, _storage = client_and_store
    value = base64.b64encode(b"initval").decode("utf-8")
    put = client.post(
        "/api/v1/secrets",
        json={"name": "itest", "value": value, "metadata": {"owner": "ci"}},
    )
    assert put.status_code == 200, put.text[:300]
    resp = client.get("/api/v1/secrets/audit")
    assert resp.status_code == 200, resp.text[:300]
    events = resp.json()["audit"]
    assert len(events) == 1
    assert events[0]["action"] == "put"
    assert events[0]["name"] == "itest"


def test_get_secret_still_works_for_normal_names(
    client_and_store: tuple[TestClient, SecretsStore, MemoryStorage],
) -> None:
    client, _store, _storage = client_and_store
    value = base64.b64encode(b"initval").decode("utf-8")
    client.post(
        "/api/v1/secrets",
        json={"name": "db-pass", "value": value, "metadata": {"env": "prod"}},
    )
    meta = client.get("/api/v1/secrets/db-pass")
    assert meta.status_code == 200, meta.text[:300]
    assert meta.json()["metadata"] == {"env": "prod"}

    revealed = client.get("/api/v1/secrets/db-pass/value")
    assert revealed.status_code == 200, revealed.text[:300]
    assert base64.b64decode(revealed.json()["value"]) == b"initval"

    missing = client.get("/api/v1/secrets/nope")
    assert missing.status_code == 404, missing.text[:300]


def test_non_dict_entry_returns_404_not_500(
    client_and_store: tuple[TestClient, SecretsStore, MemoryStorage],
) -> None:
    client, _store, storage = client_and_store
    storage.put("secrets:weird", json.dumps([1, 2, 3]).encode("utf-8"))
    resp = client.get("/api/v1/secrets/weird")
    assert resp.status_code == 404, resp.text[:300]
    assert "list" not in resp.text or resp.json()["detail"] == "not found"


def test_get_secret_raises_typed_error_for_non_dict_entry() -> None:
    storage = MemoryStorage()
    store = SecretsStore(storage=storage)
    storage.put("secrets:weird", json.dumps(["a", "b"]).encode("utf-8"))
    with pytest.raises(ValueError, match="expected JSON object, got list"):
        store.get_secret("weird")


def test_audit_route_registered_before_path_template() -> None:
    audit_index: int | None = None
    template_index: int | None = None
    for index, route in enumerate(secrets_module.secrets_router.routes):
        if route.path == "/api/v1/secrets/audit":
            audit_index = index
        elif route.path == "/api/v1/secrets/{name}":
            template_index = index
    assert audit_index is not None, "literal audit route missing"
    assert template_index is not None, "template route missing"
    assert audit_index < template_index, (
        "literal GET /secrets/audit must be declared before GET /secrets/{name}"
    )
