"""Malformed notification ids must answer 404, never a misleading 503 (issue #592).

The Mongo repository parsed ids with a bare ``ObjectId()`` inside a catch-all
that re-raised every parse failure as ``NotificationStoreError``, which the
router maps to 503 "notifications store unavailable" — classifying bad client
input as a Mongo outage. These tests run the API over the REAL repository
backed by the in-memory FakeDB, so the ObjectId parsing path is exercised
end-to-end: malformed and unknown ids degrade to 404, while genuine store
failures keep answering 503.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.mongo.notification_repository import (
    NotificationMongoRepository,
)
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.models.notification import (
    Notification,
    NotificationSeverity,
    NotificationType,
)
from tests.unit.test_notification_model import FakeDB

MALFORMED = "not-a-real-id"
UNKNOWN_OID = "aaaaaaaaaaaaaaaaaaaaaaaa"  # valid ObjectId format, absent


def _headers(user_id: str) -> dict[str, str]:
    tokens = issue_tokens({"id": user_id, "username": user_id})
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def _seed(env: SimpleNamespace) -> str:
    note = Notification.model_validate(
        {
            "user_id": "alice",
            "type": NotificationType.MENTION,
            "severity": NotificationSeverity.INFO,
            "title": "seed title",
            "message": "seed message",
            "channel": "mention",
        }
    )
    doc = note.to_document()
    doc["_id"] = ObjectId()
    env.db.notifications.docs.append(doc)
    return str(doc["_id"])


@pytest.fixture()
def env(monkeypatch: pytest.MonkeyPatch) -> Any:
    for name in (
        "TASKER_AUTH_ENABLED",
        "TASKER_API_KEY",
        "TASKER_MONGO_URL",
        "TASKER_REDIS_URL",
        "TASKER_DATABASE_URL",
        "TASKER_INTEGRATION",
    ):
        monkeypatch.delenv(name, raising=False)
    app = create_app()
    db = FakeDB()
    app.state.notification_repository = NotificationMongoRepository(database=db)
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, db=db)


def test_mark_read_malformed_id_returns_404_not_503(env: SimpleNamespace) -> None:
    resp = env.client.patch(f"/api/v1/notifications/{MALFORMED}/read", headers=_headers("alice"))
    assert resp.status_code == 404, resp.text
    assert resp.json()["error"]["code"] == "NOT_FOUND"
    assert resp.json()["error"]["message"] == "notification not found"
    assert "store unavailable" not in resp.text


def test_delete_malformed_id_returns_404_not_503(env: SimpleNamespace) -> None:
    resp = env.client.delete(f"/api/v1/notifications/{MALFORMED}", headers=_headers("alice"))
    assert resp.status_code == 404, resp.text
    assert resp.json()["error"]["code"] == "NOT_FOUND"
    assert resp.json()["error"]["message"] == "notification not found"
    assert "store unavailable" not in resp.text


def test_mark_read_unknown_valid_objectid_returns_404(env: SimpleNamespace) -> None:
    resp = env.client.patch(f"/api/v1/notifications/{UNKNOWN_OID}/read", headers=_headers("alice"))
    assert resp.status_code == 404, resp.text


def test_happy_path_mark_read_and_delete_with_real_objectids(env: SimpleNamespace) -> None:
    note_id = _seed(env)

    resp = env.client.patch(f"/api/v1/notifications/{note_id}/read", headers=_headers("alice"))
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["read"] is True

    resp = env.client.delete(f"/api/v1/notifications/{note_id}", headers=_headers("alice"))
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"] == {"id": note_id, "deleted": True}


def test_real_store_failure_still_returns_503(env: SimpleNamespace) -> None:
    note_id = _seed(env)
    env.db.notifications.fail_on = {"update_one"}

    resp = env.client.patch(f"/api/v1/notifications/{note_id}/read", headers=_headers("alice"))
    assert resp.status_code == 503, resp.text
    assert "store unavailable" in resp.json()["error"]["message"]


def test_delete_store_failure_still_returns_503(env: SimpleNamespace) -> None:
    note_id = _seed(env)
    env.db.notifications.fail_on = {"delete_one"}

    resp = env.client.delete(f"/api/v1/notifications/{note_id}", headers=_headers("alice"))
    assert resp.status_code == 503, resp.text


def test_list_and_bulk_endpoints_still_200(env: SimpleNamespace) -> None:
    _seed(env)
    assert env.client.get("/api/v1/notifications", headers=_headers("alice")).status_code == 200
    assert (
        env.client.post("/api/v1/notifications/mark-all-read", headers=_headers("alice")).status_code
        == 200
    )
    assert (
        env.client.post("/api/v1/notifications/clear-all", headers=_headers("alice")).status_code
        == 200
    )
