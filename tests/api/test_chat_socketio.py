"""Socket.IO realtime chat tests (issue #541).

Drives the real ``ChatSocketIOServer`` through ``socketio.ASGIApp`` using the
in-memory ASGI websocket transport of Starlette's ``TestClient`` (python-socketio
no longer ships ``test_client`` since v5): no network, no containers. The
handshake, room guards and 2-client broadcast run against a fake in-memory
repository, and one test proves REST (#539) reaches connected socket rooms.
"""

from __future__ import annotations

import json
import time
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.auth import tokens as tokens_module
from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.socketio_server import ChatSocketIOServer
from test_chat_endpoints import CONV_ID, OTHER_CONV_ID, FakeChatRepository, _headers, _message

SOCKET_URL = "/socket.io/?EIO=4&transport=websocket"
UPGRADE_HEADERS = {"upgrade": "websocket"}


def _token(user_id: str) -> str:
    return issue_tokens({"id": user_id, "username": user_id})["access_token"]


def _expired_token(user_id: str) -> str:
    claims = tokens_module._access_claims({"id": user_id, "username": user_id})
    claims["exp"] = int(time.time()) - 5
    return tokens_module._sign(claims)


class Wire:
    """Manual Engine.IO/Socket.IO framing over an in-memory ASGI websocket."""

    def __init__(self, ws: Any) -> None:
        self._ws = ws
        self._ack_seq = 0
        self.events: list[tuple[str, Any]] = []

    def _recv(self) -> str:
        frame = self._ws.receive_text()
        if frame == "2":
            self._ws.send_text("3")
            return self._recv()
        return frame

    def handshake(self, token: str | None) -> dict[str, Any]:
        open_frame = self._recv()
        assert open_frame.startswith("0"), open_frame
        if token is None:
            self._ws.send_text("40")
        else:
            self._ws.send_text('40{"token":"%s"}' % token)
        frame = self._recv()
        assert frame.startswith("40"), frame
        return json.loads(frame[2:])

    def handshake_rejected(self, token: str | None) -> str:
        open_frame = self._recv()
        assert open_frame.startswith("0"), open_frame
        if token is None:
            self._ws.send_text("40")
        else:
            self._ws.send_text('40{"token":"%s"}' % token)
        frame = self._recv()
        assert frame.startswith("44"), frame
        return frame

    def emit(self, event: str, data: dict[str, Any]) -> int:
        self._ack_seq += 1
        payload = json.dumps([event, data], separators=(",", ":"))
        self._ws.send_text(f"42{self._ack_seq}{payload}")
        return self._ack_seq

    def _stash_event(self, frame: str) -> None:
        payload = json.loads(frame[2:])
        if isinstance(payload, list) and len(payload) >= 2:
            self.events.append((str(payload[0]), payload[1]))

    def ack(self, seq: int) -> dict[str, Any]:
        prefix = f"43{seq}"
        while True:
            frame = self._recv()
            if frame.startswith(prefix):
                args = json.loads(frame[len(prefix) :])
                return args[0] if isinstance(args, list) else args
            assert frame.startswith("42"), f"unexpected frame while waiting for ack {seq}: {frame}"
            self._stash_event(frame)

    def event(self, name: str) -> Any:
        for index, (existing, payload) in enumerate(self.events):
            if existing == name:
                return self.events.pop(index)[1]
        while True:
            frame = self._recv()
            assert frame.startswith("42"), f"unexpected frame while waiting for {name}: {frame}"
            self._stash_event(frame)
            if self.events and self.events[-1][0] == name:
                return self.events.pop()[1]

    def drained_event_names(self) -> list[str]:
        return [name for name, _ in self.events]


@pytest.fixture()
def socket_env(monkeypatch: pytest.MonkeyPatch):
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
    server = ChatSocketIOServer(repository=repository)
    app.state.chat_repository = repository
    app.state.chat_socket = server
    with TestClient(server.asgi(app)) as client:
        yield SimpleNamespace(client=client, repo=repository, server=server)


def test_handshake_registers_authenticated_user(socket_env: SimpleNamespace) -> None:
    with socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws:
        wire = Wire(ws)
        connect = wire.handshake(_token("alice"))
        assert "sid" in connect
        assert list(socket_env.server._users.values()) == ["alice"]


def test_handshake_rejects_missing_token(socket_env: SimpleNamespace) -> None:
    with socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws:
        wire = Wire(ws)
        frame = wire.handshake_rejected(None)
        assert "authentication failed" in frame
        assert socket_env.server._users == {}


def test_handshake_rejects_invalid_token(socket_env: SimpleNamespace) -> None:
    with socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws:
        wire = Wire(ws)
        frame = wire.handshake_rejected("not-a-jwt")
        assert "authentication failed" in frame
        assert socket_env.server._users == {}


def test_handshake_rejects_expired_token(socket_env: SimpleNamespace) -> None:
    with socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws:
        wire = Wire(ws)
        frame = wire.handshake_rejected(_expired_token("alice"))
        assert "authentication failed" in frame
        assert socket_env.server._users == {}


def test_join_room_ack_and_participant_guard(socket_env: SimpleNamespace) -> None:
    with socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws:
        wire = Wire(ws)
        wire.handshake(_token("alice"))

        seq = wire.emit("join_room", {"conversation_id": CONV_ID})
        assert wire.ack(seq) == {
            "data": {"conversationId": CONV_ID, "joined": True},
            "error": None,
        }

        seq = wire.emit("join_room", {"conversationId": OTHER_CONV_ID})
        assert wire.ack(seq)["error"] == {
            "code": "FORBIDDEN",
            "message": "user is not a participant of this conversation",
        }

        seq = wire.emit("join_room", {"conversation_id": "not-an-id"})
        assert wire.ack(seq)["error"]["code"] == "VALIDATION_ERROR"

        seq = wire.emit("join_room", {"conversation_id": "64b1000000000000000000ff"})
        assert wire.ack(seq)["error"]["code"] == "NOT_FOUND"

        seq = wire.emit("join_room", {})
        assert wire.ack(seq)["error"]["code"] == "VALIDATION_ERROR"


def test_two_clients_share_room_and_persist_message(socket_env: SimpleNamespace) -> None:
    with (
        socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws_a,
        socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws_b,
    ):
        alice = Wire(ws_a)
        bob = Wire(ws_b)
        alice.handshake(_token("alice"))
        bob.handshake(_token("bob"))
        for wire in (alice, bob):
            seq = wire.emit("join_room", {"conversation_id": CONV_ID})
            assert wire.ack(seq)["error"] is None

        seq = alice.emit("send_message", {"conversation_id": CONV_ID, "text": "hola desde A"})
        payload = alice.ack(seq)["data"]
        assert payload["conversationId"] == CONV_ID
        assert payload["senderId"] == "alice"
        assert payload["content"] == "hola desde A"
        assert payload["readBy"] == ["alice"]
        assert payload["id"]

        assert alice.event("new_message") == payload
        assert bob.event("new_message") == payload

        stored = socket_env.repo.messages[-1]
        assert stored["sender_id"] == "alice"
        assert stored["text"] == "hola desde A"
        assert stored["conversation_id"] == CONV_ID


def test_typing_reaches_room_members_except_sender(socket_env: SimpleNamespace) -> None:
    with (
        socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws_a,
        socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws_b,
    ):
        alice = Wire(ws_a)
        bob = Wire(ws_b)
        alice.handshake(_token("alice"))
        bob.handshake(_token("bob"))
        for wire in (alice, bob):
            seq = wire.emit("join_room", {"conversation_id": CONV_ID})
            assert wire.ack(seq)["error"] is None

        seq = alice.emit("typing_start", {"conversation_id": CONV_ID})
        assert alice.ack(seq) == {
            "data": {"conversationId": CONV_ID, "typing": True},
            "error": None,
        }
        assert alice.drained_event_names() == []
        assert bob.event("typing_start") == {"conversationId": CONV_ID, "userId": "alice"}

        seq = alice.emit("typing_stop", {"conversation_id": CONV_ID})
        assert alice.ack(seq)["data"]["typing"] is False
        assert alice.drained_event_names() == []
        assert bob.event("typing_stop") == {"conversationId": CONV_ID, "userId": "alice"}


def test_mark_as_read_persists_and_broadcasts(socket_env: SimpleNamespace) -> None:
    socket_env.repo.messages.append(_message(CONV_ID, "alice", "uno", "m1"))
    socket_env.repo.messages.append(_message(CONV_ID, "alice", "dos", "m2"))
    with (
        socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws_a,
        socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws_b,
    ):
        alice = Wire(ws_a)
        bob = Wire(ws_b)
        alice.handshake(_token("alice"))
        bob.handshake(_token("bob"))
        for wire in (alice, bob):
            seq = wire.emit("join_room", {"conversation_id": CONV_ID})
            assert wire.ack(seq)["error"] is None

        seq = bob.emit("mark_as_read", {"conversation_id": CONV_ID})
        ack = bob.ack(seq)
        assert ack["data"] == {
            "conversationId": CONV_ID,
            "userId": "bob",
            "matchedCount": 2,
        }
        expected = {"conversationId": CONV_ID, "userId": "bob", "matchedCount": 2}
        assert alice.event("messages_read") == expected
        assert bob.event("messages_read") == expected
        assert all("bob" in message["read_by"] for message in socket_env.repo.messages)


def test_send_message_rejects_invalid_payload_and_strangers(socket_env: SimpleNamespace) -> None:
    with socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws:
        wire = Wire(ws)
        wire.handshake(_token("alice"))
        seq = wire.emit("join_room", {"conversation_id": CONV_ID})
        assert wire.ack(seq)["error"] is None

        seq = wire.emit("send_message", {"conversation_id": CONV_ID, "text": ""})
        assert wire.ack(seq)["error"]["code"] == "VALIDATION_ERROR"

        seq = wire.emit("send_message", {"conversation_id": CONV_ID, "text": "x", "type": "gif"})
        assert wire.ack(seq)["error"]["code"] == "VALIDATION_ERROR"

    with socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws:
        wire = Wire(ws)
        wire.handshake(_token("carol"))
        seq = wire.emit("send_message", {"conversation_id": CONV_ID, "text": "intruso"})
        assert wire.ack(seq)["error"]["code"] == "FORBIDDEN"
        assert socket_env.repo.messages == []


def test_rest_message_reaches_connected_room_member(socket_env: SimpleNamespace) -> None:
    with socket_env.client.websocket_connect(SOCKET_URL, headers=UPGRADE_HEADERS) as ws:
        wire = Wire(ws)
        wire.handshake(_token("bob"))
        seq = wire.emit("join_room", {"conversation_id": CONV_ID})
        assert wire.ack(seq)["error"] is None

        resp = socket_env.client.post(
            f"/api/v1/chat/conversations/{CONV_ID}/messages",
            json={"text": "por REST"},
            headers=_headers("alice"),
        )
        assert resp.status_code == 200
        rest_payload = resp.json()["data"]
        assert rest_payload["senderId"] == "alice"
        assert wire.event("new_message") == rest_payload
