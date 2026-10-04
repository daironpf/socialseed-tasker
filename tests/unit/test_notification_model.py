"""Notification model/repository unit tests (issue #547).

Runs against an in-process fake of the motor database — no real MongoDB —
and verifies the safe fallback when TASKER_MONGO_URL is not configured.
"""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient
from pydantic import ValidationError

from socialseed_tasker.infrastructure.mongo import client as mongo_client
from socialseed_tasker.infrastructure.mongo.client import (
    close_mongo,
    ensure_notification_indexes,
    get_chat_database,
    get_mongo_client,
)
from socialseed_tasker.infrastructure.mongo.notification_repository import (
    NotificationMongoRepository,
    NotificationStoreError,
)
from socialseed_tasker.models.notification import (
    FRONTEND_CATEGORIES,
    NOTIFICATIONS_COLLECTION,
    Notification,
    NotificationSeverity,
    NotificationType,
)


def _matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    return all(doc.get(key) == cond for key, cond in query.items())


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict[str, Any]] = []
        self.indexes: list[Any] = []
        self.fail_on: set[str] = set()

    async def find_one(self, query: dict[str, Any]) -> dict[str, Any] | None:
        if "find_one" in self.fail_on:
            raise RuntimeError("mongo down")
        hits = [d for d in self.docs if _matches(d, query)]
        return dict(hits[0]) if hits else None

    async def insert_one(self, doc: dict[str, Any]) -> SimpleNamespace:
        if "insert_one" in self.fail_on:
            raise RuntimeError("mongo down")
        stored = dict(doc)
        stored.setdefault("_id", ObjectId())
        self.docs.append(stored)
        return SimpleNamespace(inserted_id=stored["_id"])

    async def create_index(self, keys: Any) -> str:
        self.indexes.append(keys)
        return "notification-index"


class FakeDB:
    def __init__(self) -> None:
        self.notifications = FakeCollection()

    def __getitem__(self, name: str) -> FakeCollection:
        assert name == NOTIFICATIONS_COLLECTION
        return self.notifications


@pytest.fixture(autouse=True)
def _reset_mongo_cache() -> Any:
    close_mongo()
    yield
    close_mongo()


@pytest.fixture
def mongo_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TASKER_MONGO_URL", raising=False)
    monkeypatch.delenv("TASKER_MONGO_DB", raising=False)
    close_mongo()


@pytest.fixture
def db() -> FakeDB:
    return FakeDB()


@pytest.fixture
def repo(db: FakeDB) -> NotificationMongoRepository:
    return NotificationMongoRepository(database=db)


def _sample(**overrides: Any) -> Notification:
    payload: dict[str, Any] = {
        "user_id": "alice",
        "type": NotificationType.HITL,
        "severity": NotificationSeverity.WARNING,
        "title": "Approval needed",
        "message": "Approve the run before it continues",
        "channel": "hitl",
        "link_to": "/issues/1",
        "hitl_request_id": "req-1",
    }
    payload.update(overrides)
    return Notification.model_validate(payload)


def test_notification_defaults_and_category() -> None:
    note = _sample()
    assert note.id is None
    assert note.read is False
    assert note.requires_action is False
    assert note.link_to == "/issues/1"
    assert note.hitl_request_id == "req-1"
    assert note.created_at.tzinfo is not None
    assert note.created_at.utcoffset() == timezone.utc.utcoffset(None)
    assert note.category == "hitl"
    assert note.type is NotificationType.HITL
    assert note.severity is NotificationSeverity.WARNING


def test_notification_validation_rejects_invalid_input() -> None:
    with pytest.raises(ValidationError):
        _sample(type="NOT_A_TYPE")
    with pytest.raises(ValidationError):
        _sample(severity="CRITICAL")
    with pytest.raises(ValidationError):
        _sample(user_id="")
    with pytest.raises(ValidationError):
        _sample(title="")


def test_naive_created_at_is_normalized_to_utc() -> None:
    note = _sample(created_at=datetime(2026, 1, 1, 12, 0, 0))
    assert note.created_at.tzinfo is not None
    assert note.created_at.utcoffset() == timezone.utc.utcoffset(None)


def test_frontend_categories_cover_every_type() -> None:
    assert set(FRONTEND_CATEGORIES) == set(NotificationType)
    existing_frontend = {"mention", "hitl", "constraint_violation", "agent_failure", "sla"}
    assert set(FRONTEND_CATEGORIES.values()) == existing_frontend | {"welcome"}
    assert FRONTEND_CATEGORIES[NotificationType.MENTION] == "mention"
    assert FRONTEND_CATEGORIES[NotificationType.HITL] == "hitl"
    assert FRONTEND_CATEGORIES[NotificationType.CONSTRAINT_VIOLATION] == "constraint_violation"
    assert FRONTEND_CATEGORIES[NotificationType.AGENT_FAILURE] == "agent_failure"
    assert FRONTEND_CATEGORIES[NotificationType.SLA] == "sla"
    assert FRONTEND_CATEGORIES[NotificationType.WELCOME] == "welcome"


def test_to_document_and_from_document_round_trip() -> None:
    note = _sample()
    doc = note.to_document()
    assert "id" not in doc
    assert "_id" not in doc
    assert doc["type"] == "HITL"
    assert doc["severity"] == "WARNING"
    assert isinstance(doc["created_at"], datetime)
    assert doc["read"] is False

    stored = dict(doc)
    stored["_id"] = ObjectId()
    restored = Notification.from_document(stored)
    assert restored is not None
    assert restored.id == str(stored["_id"])
    assert restored.user_id == "alice"
    assert restored.type is NotificationType.HITL
    assert restored.created_at == note.created_at

    iso_doc = dict(doc)
    iso_doc["created_at"] = note.created_at.isoformat()
    from_iso = Notification.from_document(iso_doc)
    assert from_iso is not None
    assert from_iso.created_at == note.created_at

    assert Notification.from_document(None) is None
    assert Notification.from_document({}) is None


async def test_insert_and_read_document(repo: NotificationMongoRepository, db: FakeDB) -> None:
    inserted = await repo.insert(_sample())
    assert isinstance(inserted.id, str)
    assert len(db.notifications.docs) == 1
    assert db.notifications.docs[0]["type"] == "HITL"
    assert "_id" in db.notifications.docs[0]

    found = await repo.get(inserted.id)
    assert found is not None
    assert found.id == inserted.id
    assert found.title == "Approval needed"
    assert found.user_id == "alice"
    assert found.channel == "hitl"
    assert found.created_at.tzinfo is not None
    assert await repo.get(str(ObjectId())) is None


async def test_get_validates_id(repo: NotificationMongoRepository) -> None:
    with pytest.raises(NotificationStoreError, match="notification_id is required"):
        await repo.get("")
    with pytest.raises(NotificationStoreError, match="invalid document id"):
        await repo.get("not-an-object-id")


async def test_not_configured_operations_raise(mongo_off: None) -> None:
    repo_nc = NotificationMongoRepository()
    assert get_mongo_client() is None
    assert get_chat_database() is None
    with pytest.raises(NotificationStoreError, match="TASKER_MONGO_URL"):
        await repo_nc.insert(_sample())
    with pytest.raises(NotificationStoreError, match="TASKER_MONGO_URL"):
        await repo_nc.get("507f1f77bcf86cd799439011")


async def test_operation_failure_degrades_to_typed_error(db: FakeDB) -> None:
    db.notifications.fail_on = {"insert_one"}
    repo_fail = NotificationMongoRepository(database=db)
    with pytest.raises(NotificationStoreError, match="insert notification failed"):
        await repo_fail.insert(_sample())
    db.notifications.fail_on = {"find_one"}
    with pytest.raises(NotificationStoreError, match="get notification failed"):
        await repo_fail.get("507f1f77bcf86cd799439011")


async def test_ensure_notification_indexes_false_without_env(mongo_off: None) -> None:
    assert await ensure_notification_indexes() is False


async def test_ensure_notification_indexes_idempotent(db: FakeDB, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mongo_client, "get_chat_database", lambda: db)
    assert await ensure_notification_indexes() is True
    assert await ensure_notification_indexes() is True
    assert db.notifications.indexes.count([("user_id", 1), ("read", 1)]) == 2
    assert db.notifications.indexes.count([("created_at", -1)]) == 2


def test_lifespan_bootstraps_notification_indexes(monkeypatch: pytest.MonkeyPatch) -> None:
    from socialseed_tasker.infrastructure.web_api.app import create_app

    called: dict[str, bool] = {}

    async def _chat() -> bool:
        called["chat"] = True
        return True

    async def _notifications() -> bool:
        called["notifications"] = True
        return True

    monkeypatch.delenv("TASKER_MONGO_URL", raising=False)
    close_mongo()
    monkeypatch.setattr(mongo_client, "get_mongo_client", lambda: object())
    monkeypatch.setattr(mongo_client, "ensure_chat_indexes", _chat)
    monkeypatch.setattr(mongo_client, "ensure_notification_indexes", _notifications)
    with TestClient(create_app()) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    assert called.get("chat") is True
    assert called.get("notifications") is True
