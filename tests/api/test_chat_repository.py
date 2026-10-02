"""Chat MongoDB schema/repository unit tests (issue #537).

Runs against an in-process fake of the motor database — no real MongoDB —
and verifies the safe fallback when TASKER_MONGO_URL is not configured.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from bson import ObjectId
from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.mongo import client as mongo_client
from socialseed_tasker.infrastructure.mongo.chat_repository import (
    ChatMongoRepository,
    ChatStoreError,
)
from socialseed_tasker.infrastructure.mongo.client import (
    close_mongo,
    ensure_chat_indexes,
    get_chat_database,
    get_mongo_client,
)


class FakeCursor:
    def __init__(self, docs: list[dict[str, Any]]) -> None:
        self._docs = list(docs)

    def sort(self, key: str, direction: int = -1) -> FakeCursor:
        self._docs.sort(key=lambda d: d.get(key), reverse=direction == -1)
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, Any]]:
        if length is None:
            return list(self._docs)
        return self._docs[:length]


def _matches(doc: dict[str, Any], query: dict[str, Any]) -> bool:
    for key, cond in query.items():
        value = doc.get(key)
        if isinstance(cond, dict):
            if "$all" in cond and not all(v in (value or []) for v in cond["$all"]):
                return False
            if "$size" in cond and len(value or []) != cond["$size"]:
                return False
            if "$lt" in cond and (value is None or not value < cond["$lt"]):
                return False
        elif key == "participant_ids" and isinstance(cond, str):
            if cond not in (value or []):
                return False
        elif value != cond:
            return False
    return True


def _apply_update(doc: dict[str, Any], update: dict[str, Any]) -> None:
    for op, fields in update.items():
        if op == "$set":
            doc.update(fields)
        elif op == "$addToSet":
            for field, value in fields.items():
                arr = doc.setdefault(field, [])
                if value not in arr:
                    arr.append(value)
        elif op == "$pull":
            for field, value in fields.items():
                doc[field] = [v for v in doc.get(field, []) if v != value]


class FakeCollection:
    def __init__(self) -> None:
        self.docs: list[dict[str, Any]] = []
        self.indexes: list[Any] = []
        self.fail_on: set[str] = set()

    def find(self, query: dict[str, Any]) -> FakeCursor:
        if "find" in self.fail_on:
            raise RuntimeError("mongo down")
        return FakeCursor([d for d in self.docs if _matches(d, query)])

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

    async def update_one(self, query: dict[str, Any], update: dict[str, Any]) -> SimpleNamespace:
        if "update_one" in self.fail_on:
            raise RuntimeError("mongo down")
        hits = [d for d in self.docs if _matches(d, query)]
        for doc in hits[:1]:
            _apply_update(doc, update)
        return SimpleNamespace(matched_count=min(len(hits), 1), modified_count=min(len(hits), 1))

    async def update_many(self, query: dict[str, Any], update: dict[str, Any]) -> SimpleNamespace:
        if "update_many" in self.fail_on:
            raise RuntimeError("mongo down")
        hits = [d for d in self.docs if _matches(d, query)]
        for doc in hits:
            _apply_update(doc, update)
        return SimpleNamespace(matched_count=len(hits), modified_count=len(hits))

    async def create_index(self, keys: Any) -> str:
        self.indexes.append(keys)
        return "chat-index"


class FakeDB:
    def __init__(self) -> None:
        self.conversations = FakeCollection()
        self.messages = FakeCollection()

    def __getitem__(self, name: str) -> FakeCollection:
        return getattr(self, name)


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
def repo(db: FakeDB) -> ChatMongoRepository:
    return ChatMongoRepository(database=db)


def test_client_none_without_env(mongo_off: None) -> None:
    assert get_mongo_client() is None
    assert get_chat_database() is None


async def test_ensure_indexes_false_without_env(mongo_off: None) -> None:
    assert await ensure_chat_indexes() is False


async def test_ensure_indexes_idempotent(db: FakeDB, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(mongo_client, "get_chat_database", lambda: db)
    assert await ensure_chat_indexes() is True
    assert await ensure_chat_indexes() is True
    assert db.conversations.indexes.count([("participant_ids", 1)]) == 2
    assert db.messages.indexes.count([("conversation_id", 1)]) == 2
    assert db.messages.indexes.count([("conversation_id", 1), ("created_at", -1)]) == 2
    assert db.messages.indexes.count([("created_at", -1)]) == 2


async def test_not_configured_operations_raise(mongo_off: None) -> None:
    repo_nc = ChatMongoRepository()
    with pytest.raises(ChatStoreError, match="TASKER_MONGO_URL"):
        await repo_nc.list_conversations("user-1")
    with pytest.raises(ChatStoreError, match="TASKER_MONGO_URL"):
        await repo_nc.insert_message("c1", "user-1", "hi")


async def test_operation_failure_degrades_to_typed_error(db: FakeDB) -> None:
    db.messages.fail_on = {"find"}
    repo_fail = ChatMongoRepository(database=db)
    with pytest.raises(ChatStoreError, match="list messages failed"):
        await repo_fail.list_messages("c1")


async def test_list_conversations_filters_and_orders(repo: ChatMongoRepository, db: FakeDB) -> None:
    now = datetime.now(timezone.utc)
    db.conversations.docs = [
        {"_id": ObjectId(), "type": "direct", "participant_ids": ["alice", "bob"],
         "pinned_by": [], "updated_at": now - timedelta(minutes=5), "created_at": now},
        {"_id": ObjectId(), "type": "group", "participant_ids": ["alice", "carol"],
         "pinned_by": [], "updated_at": now, "created_at": now},
        {"_id": ObjectId(), "type": "direct", "participant_ids": ["bob", "carol"],
         "pinned_by": [], "updated_at": now, "created_at": now},
    ]
    convs = await repo.list_conversations("alice")
    assert [c["id"] for c in convs] == [
        str(db.conversations.docs[1]["_id"]),
        str(db.conversations.docs[0]["_id"]),
    ]
    assert all("alice" in c["participant_ids"] for c in convs)


async def test_create_or_get_direct_reuses_existing_pair(repo: ChatMongoRepository, db: FakeDB) -> None:
    created = await repo.create_or_get_conversation(["bob", "alice"], "direct")
    again = await repo.create_or_get_conversation(["alice", "bob"], "direct")
    assert created["id"] == again["id"]
    assert len(db.conversations.docs) == 1
    assert created["participant_ids"] == ["alice", "bob"]
    assert created["type"] == "direct"
    assert created["pinned_by"] == []
    assert datetime.fromisoformat(created["created_at"]).tzinfo is not None


async def test_create_or_get_group_always_creates(repo: ChatMongoRepository, db: FakeDB) -> None:
    first = await repo.create_or_get_conversation(["alice", "bob", "carol"], "group", title="squad")
    second = await repo.create_or_get_conversation(["alice", "bob", "carol"], "group", title="squad")
    assert first["id"] != second["id"]
    assert len(db.conversations.docs) == 2
    assert first["title"] == "squad"


async def test_create_or_get_validates_input(repo: ChatMongoRepository) -> None:
    with pytest.raises(ChatStoreError, match="participant_ids"):
        await repo.create_or_get_conversation([], "direct")
    with pytest.raises(ChatStoreError, match="invalid conversation type"):
        await repo.create_or_get_conversation(["a", "b"], "secret")


async def test_insert_message_schema_and_bump(repo: ChatMongoRepository, db: FakeDB) -> None:
    conv = await repo.create_or_get_conversation(["alice", "bob"], "direct")
    before = datetime.fromisoformat(conv["updated_at"])
    msg = await repo.insert_message(conv["id"], "alice", "hola", "text")
    assert isinstance(msg["id"], str)
    assert msg["conversation_id"] == conv["id"]
    assert msg["sender_id"] == "alice"
    assert msg["text"] == "hola"
    assert msg["type"] == "text"
    assert msg["read_by"] == ["alice"]
    assert msg["reactions"] == []
    assert datetime.fromisoformat(msg["created_at"]) >= before
    stored_conv = await db.conversations.find_one({"_id": ObjectId(conv["id"])})
    assert stored_conv is not None
    assert stored_conv["updated_at"] >= before


async def test_insert_message_validates(repo: ChatMongoRepository) -> None:
    with pytest.raises(ChatStoreError, match="invalid message type"):
        await repo.insert_message("c1", "alice", "hi", "audio")
    with pytest.raises(ChatStoreError, match="text is required"):
        await repo.insert_message("c1", "alice", "")


async def test_list_messages_pagination_before(repo: ChatMongoRepository, db: FakeDB) -> None:
    now = datetime.now(timezone.utc)
    for i in range(3):
        db.messages.docs.append(
            {
                "_id": ObjectId(),
                "conversation_id": "conv-1",
                "sender_id": "alice",
                "text": f"m{i}",
                "type": "text",
                "read_by": ["alice"],
                "reactions": [],
                "created_at": now + timedelta(seconds=i),
            }
        )
    page = await repo.list_messages("conv-1")
    assert [m["text"] for m in page] == ["m0", "m1", "m2"]
    older = await repo.list_messages("conv-1", before=(now + timedelta(seconds=1)).isoformat())
    assert [m["text"] for m in older] == ["m0"]
    with pytest.raises(ChatStoreError, match="invalid before cursor"):
        await repo.list_messages("conv-1", before="not-a-date")


async def test_toggle_pin_add_and_remove(repo: ChatMongoRepository, db: FakeDB) -> None:
    conv = await repo.create_or_get_conversation(["alice", "bob"], "direct")
    pinned = await repo.toggle_pin(conv["id"], "alice")
    assert pinned["pinned_by"] == ["alice"]
    unpinned = await repo.toggle_pin(conv["id"], "alice")
    assert unpinned["pinned_by"] == []
    with pytest.raises(ChatStoreError, match="conversation not found"):
        await repo.toggle_pin(str(ObjectId()), "alice")


async def test_mark_as_read_idempotent(repo: ChatMongoRepository) -> None:
    conv = await repo.create_or_get_conversation(["alice", "bob"], "direct")
    await repo.insert_message(conv["id"], "alice", "m1")
    await repo.insert_message(conv["id"], "bob", "m2")
    first = await repo.mark_as_read(conv["id"], "bob")
    second = await repo.mark_as_read(conv["id"], "bob")
    assert first["matched_count"] == 2
    assert second["matched_count"] == 2
    msgs = await repo.list_messages(conv["id"])
    assert all("bob" in m["read_by"] for m in msgs)
    assert all(m["read_by"].count("bob") == 1 for m in msgs)


async def test_set_reaction_toggles(repo: ChatMongoRepository) -> None:
    conv = await repo.create_or_get_conversation(["alice", "bob"], "direct")
    msg = await repo.insert_message(conv["id"], "alice", "m1")
    reacted = await repo.set_reaction(conv["id"], msg["id"], "bob", "\U0001f44d")
    assert reacted["reactions"] == [{"user_id": "bob", "emoji": "\U0001f44d"}]
    removed = await repo.set_reaction(conv["id"], msg["id"], "bob", "\U0001f44d")
    assert removed["reactions"] == []
    with pytest.raises(ChatStoreError, match="emoji is required"):
        await repo.set_reaction(conv["id"], msg["id"], "bob", "")


def test_health_api_without_mongo(monkeypatch: pytest.MonkeyPatch) -> None:
    from socialseed_tasker.infrastructure.web_api.app import create_app

    monkeypatch.delenv("TASKER_MONGO_URL", raising=False)
    monkeypatch.delenv("TASKER_REDIS_URL", raising=False)
    monkeypatch.delenv("TASKER_DATABASE_URL", raising=False)
    close_mongo()
    with TestClient(create_app()) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "healthy"
    assert body["dependencies"]["neo4j"] == "not configured"
