from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.mongo.chat_repository import ChatStoreError
from socialseed_tasker.infrastructure.web_api.app import create_app

CONV_ID = "64b1000000000000000000a1"
OTHER_CONV_ID = "64b1000000000000000000b2"
UNKNOWN_CONV_ID = "64b1000000000000000000c3"


def _conversation(cid: str, participants: list[str], conversation_type: str = "direct") -> dict[str, Any]:
    return {
        "id": cid,
        "title": None,
        "type": conversation_type,
        "participant_ids": participants,
        "pinned_by": [],
        "created_at": "2026-10-01T00:00:00+00:00",
        "updated_at": "2026-10-01T00:00:00+00:00",
    }


def _message(cid: str, sender: str, text: str, msg_id: str) -> dict[str, Any]:
    return {
        "id": msg_id,
        "conversation_id": cid,
        "sender_id": sender,
        "text": text,
        "type": "text",
        "read_by": [sender],
        "reactions": [{"user_id": sender, "emoji": "\U0001f44d"}],
        "created_at": "2026-10-01T00:01:00+00:00",
    }


class FakeChatRepository:
    def __init__(self) -> None:
        self.conversations: dict[str, dict[str, Any]] = {
            CONV_ID: _conversation(CONV_ID, ["alice", "bob"]),
            OTHER_CONV_ID: _conversation(OTHER_CONV_ID, ["carol", "dave"], "group"),
        }
        self.messages: list[dict[str, Any]] = []
        self.calls: list[tuple[Any, ...]] = []
        self.degraded = False

    def _guard(self, action: str) -> None:
        if self.degraded:
            raise ChatStoreError(f"{action} unavailable")

    async def list_conversations(self, user_id: str) -> list[dict[str, Any]]:
        self._guard("list")
        return [c for c in self.conversations.values() if user_id in c["participant_ids"]]

    async def create_or_get_conversation(
        self,
        participant_ids: list[str],
        conversation_type: str = "direct",
        title: str | None = None,
    ) -> dict[str, Any]:
        self._guard("create")
        cid = "64b1" + "0" * 18 + f"{len(self.conversations):02x}"
        conversation = _conversation(cid, sorted(participant_ids), conversation_type)
        conversation["title"] = title
        self.conversations[cid] = conversation
        return conversation

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        self._guard("get")
        return self.conversations.get(conversation_id)

    async def list_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before: str | None = None,
    ) -> list[dict[str, Any]]:
        self._guard("messages")
        self.calls.append(("list_messages", conversation_id, limit, before))
        matches = [m for m in self.messages if m["conversation_id"] == conversation_id]
        return matches[-limit:]

    async def latest_message(self, conversation_id: str) -> dict[str, Any] | None:
        self._guard("latest")
        matches = [m for m in self.messages if m["conversation_id"] == conversation_id]
        return matches[-1] if matches else None

    async def toggle_pin(self, conversation_id: str, user_id: str) -> dict[str, Any]:
        self._guard("pin")
        conversation = self.conversations[conversation_id]
        if user_id in conversation["pinned_by"]:
            conversation["pinned_by"].remove(user_id)
        else:
            conversation["pinned_by"].append(user_id)
        return conversation

    async def insert_message(
        self,
        conversation_id: str,
        sender_id: str,
        text: str,
        message_type: str = "text",
    ) -> dict[str, Any]:
        self._guard("insert")
        message = _message(conversation_id, sender_id, text, f"m{len(self.messages) + 1}")
        message["type"] = message_type
        self.messages.append(message)
        return message

    async def mark_as_read(self, conversation_id: str, user_id: str) -> dict[str, Any]:
        self._guard("mark_as_read")
        matched = 0
        for message in self.messages:
            if message["conversation_id"] == conversation_id and user_id not in message["read_by"]:
                message["read_by"].append(user_id)
                matched += 1
        return {"conversation_id": conversation_id, "user_id": user_id, "matched_count": matched}


def _headers(user_id: str) -> dict[str, str]:
    tokens = issue_tokens({"id": user_id, "username": user_id})
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def chat_env(monkeypatch: pytest.MonkeyPatch):
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
    repository = FakeChatRepository()
    emitted: list[tuple[str, dict[str, Any], str]] = []

    async def _emit(event: str, data: dict[str, Any], room: str) -> None:
        emitted.append((event, data, room))

    app.state.chat_repository = repository
    app.state.chat_emit = _emit
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, repo=repository, emitted=emitted)


def test_list_conversations_requires_identity(chat_env: SimpleNamespace) -> None:
    resp = chat_env.client.get("/api/v1/chat/conversations")
    assert resp.status_code == 401


def test_list_conversations_returns_participant_wires(chat_env: SimpleNamespace) -> None:
    chat_env.repo.messages.append(_message(CONV_ID, "alice", "hola", "m1"))
    resp = chat_env.client.get("/api/v1/chat/conversations", headers=_headers("alice"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    conversations = body["data"]
    assert [c["id"] for c in conversations] == [CONV_ID]
    wire = conversations[0]
    assert wire["participantIds"] == ["alice", "bob"]
    assert wire["pinnedBy"] == []
    assert wire["lastMessage"]["content"] == "hola"
    assert wire["lastMessage"]["senderId"] == "alice"
    assert "participant_ids" not in wire
    assert "conversation_id" not in wire["lastMessage"]

    resp = chat_env.client.get("/api/v1/chat/conversations", headers=_headers("carol"))
    assert resp.status_code == 200
    assert [c["id"] for c in resp.json()["data"]] == [OTHER_CONV_ID]


def test_create_direct_and_group_validation(chat_env: SimpleNamespace) -> None:
    resp = chat_env.client.post(
        "/api/v1/chat/conversations",
        json={"participantIds": ["bob"]},
        headers=_headers("alice"),
    )
    assert resp.status_code == 200
    created = resp.json()["data"]
    assert created["type"] == "direct"
    assert created["participantIds"] == ["alice", "bob"]

    resp = chat_env.client.post(
        "/api/v1/chat/conversations",
        json={"participantIds": ["bob", "bob"]},
        headers=_headers("alice"),
    )
    assert resp.status_code == 400

    resp = chat_env.client.post(
        "/api/v1/chat/conversations",
        json={"participantIds": ["bob", "carol"]},
        headers=_headers("alice"),
    )
    assert resp.status_code == 400

    resp = chat_env.client.post(
        "/api/v1/chat/conversations",
        json={"participant_ids": ["bob"], "type": "group", "title": "sprint"},
        headers=_headers("alice"),
    )
    assert resp.status_code == 200
    group = resp.json()["data"]
    assert group["type"] == "group"
    assert group["title"] == "sprint"
    assert group["participantIds"] == ["alice", "bob"]

    resp = chat_env.client.post(
        "/api/v1/chat/conversations",
        json={"participantIds": ["bob"], "type": "secret"},
        headers=_headers("alice"),
    )
    assert resp.status_code == 400


def test_messages_history_pagination_and_forbidden(chat_env: SimpleNamespace) -> None:
    for i in range(3):
        chat_env.repo.messages.append(_message(CONV_ID, "alice", f"m{i}", f"m{i}"))

    resp = chat_env.client.get(
        f"/api/v1/chat/conversations/{CONV_ID}/messages", headers=_headers("alice")
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert [m["content"] for m in data["messages"]] == ["m0", "m1", "m2"]
    assert data["nextCursor"] is None

    resp = chat_env.client.get(
        f"/api/v1/chat/conversations/{CONV_ID}/messages?limit=2", headers=_headers("alice")
    )
    data = resp.json()["data"]
    assert [m["content"] for m in data["messages"]] == ["m1", "m2"]
    assert data["nextCursor"] == "2026-10-01T00:01:00+00:00"

    resp = chat_env.client.get(
        f"/api/v1/chat/conversations/{CONV_ID}/messages",
        params={"before": "2026-10-01T00:01:00+00:00"},
        headers=_headers("alice"),
    )
    assert resp.status_code == 200
    assert ("list_messages", CONV_ID, 50, "2026-10-01T00:01:00+00:00") in chat_env.repo.calls

    resp = chat_env.client.get(
        f"/api/v1/chat/conversations/{CONV_ID}/messages", headers=_headers("carol")
    )
    assert resp.status_code == 403

    resp = chat_env.client.get(
        f"/api/v1/chat/conversations/{UNKNOWN_CONV_ID}/messages", headers=_headers("alice")
    )
    assert resp.status_code == 404

    resp = chat_env.client.get(
        "/api/v1/chat/conversations/not-an-id/messages", headers=_headers("alice")
    )
    assert resp.status_code == 400

    resp = chat_env.client.get(
        f"/api/v1/chat/conversations/{CONV_ID}/messages",
        params={"before": "nope"},
        headers=_headers("alice"),
    )
    assert resp.status_code == 400


def test_pin_toggles_for_current_user(chat_env: SimpleNamespace) -> None:
    resp = chat_env.client.post(f"/api/v1/chat/conversations/{CONV_ID}/pin", headers=_headers("alice"))
    assert resp.status_code == 200
    assert resp.json()["data"]["pinnedBy"] == ["alice"]

    resp = chat_env.client.post(f"/api/v1/chat/conversations/{CONV_ID}/pin", headers=_headers("alice"))
    assert resp.json()["data"]["pinnedBy"] == []

    resp = chat_env.client.post(f"/api/v1/chat/conversations/{CONV_ID}/pin", headers=_headers("carol"))
    assert resp.status_code == 403


def test_create_message_persists_and_emits(chat_env: SimpleNamespace) -> None:
    resp = chat_env.client.post(
        f"/api/v1/chat/conversations/{CONV_ID}/messages",
        json={"text": " hola equipo "},
        headers=_headers("bob"),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["content"] == "hola equipo"
    assert data["senderId"] == "bob"
    assert data["conversationId"] == CONV_ID
    assert data["readBy"] == ["bob"]
    assert data["reactions"] == {"\U0001f44d": ["bob"]}
    assert len(chat_env.repo.messages) == 1
    assert chat_env.emitted == [("new_message", data, CONV_ID)]

    resp = chat_env.client.post(
        f"/api/v1/chat/conversations/{CONV_ID}/messages",
        json={"text": "   "},
        headers=_headers("bob"),
    )
    assert resp.status_code == 400

    resp = chat_env.client.post(
        f"/api/v1/chat/conversations/{CONV_ID}/messages",
        json={"text": "ok", "type": "gif"},
        headers=_headers("bob"),
    )
    assert resp.status_code == 400

    resp = chat_env.client.post(
        f"/api/v1/chat/conversations/{CONV_ID}/messages",
        json={"text": "nope"},
        headers=_headers("carol"),
    )
    assert resp.status_code == 403
    assert len(chat_env.emitted) == 1


def test_message_authorship_always_follows_token_identity(chat_env: SimpleNamespace) -> None:
    resp = chat_env.client.post(
        f"/api/v1/chat/conversations/{CONV_ID}/messages",
        json={"text": "spoof", "senderId": "mallory", "sender_id": "mallory"},
        headers=_headers("alice"),
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["senderId"] == "alice"
    assert chat_env.repo.messages[-1]["sender_id"] == "alice"

    resp = chat_env.client.post(
        f"/api/v1/chat/conversations/{CONV_ID}/messages",
        json={"text": "jwt gana"},
        headers={**_headers("alice"), "X-User-ID": "mallory"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["senderId"] == "alice"

    resp = chat_env.client.post(
        f"/api/v1/chat/conversations/{CONV_ID}/messages",
        json={"text": "solo dev header"},
        headers={"X-User-ID": "bob"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["senderId"] == "bob"


def test_conversation_creator_identity_always_follows_token(chat_env: SimpleNamespace) -> None:
    resp = chat_env.client.post(
        "/api/v1/chat/conversations",
        json={"participantIds": ["bob"]},
        headers={**_headers("alice"), "X-User-ID": "mallory"},
    )
    assert resp.status_code == 200
    created = resp.json()["data"]
    assert created["participantIds"] == ["alice", "bob"]


def test_dev_header_identity_when_auth_disabled(chat_env: SimpleNamespace) -> None:
    resp = chat_env.client.get("/api/v1/chat/conversations", headers={"X-User-ID": "alice"})
    assert resp.status_code == 200
    assert [c["id"] for c in resp.json()["data"]] == [CONV_ID]


def test_chat_store_degraded_returns_503(chat_env: SimpleNamespace) -> None:
    chat_env.repo.degraded = True
    resp = chat_env.client.get("/api/v1/chat/conversations", headers=_headers("alice"))
    assert resp.status_code == 503
    resp = chat_env.client.get(
        f"/api/v1/chat/conversations/{CONV_ID}/messages", headers=_headers("alice")
    )
    assert resp.status_code == 503
    resp = chat_env.client.post(
        f"/api/v1/chat/conversations/{CONV_ID}/pin", headers=_headers("alice")
    )
    assert resp.status_code == 503
