"""Unit tests for the DELETE endpoints added by issue #596.

Covers the three missing destroys: the skills catalog (PostgreSQL cascade
over ``user_skills``), the MCP server registry (in-process cascade of
orphaned sessions) and the chat conversation store (Mongo messages cascade
with a strict 404 that never leaks existence of foreign conversations).
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.mongo.chat_repository import ChatStoreError
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import catalogs
from tests.fakes.fake_pg_users import FakePgCursor, install_fake_pg

CONV_ID = "64b1000000000000000000a1"
UNKNOWN_CONV_ID = "64b1000000000000000000c3"


# ---------------------------------------------------------------------------
# DELETE /skills/{skill_id} (issue #596)
# ---------------------------------------------------------------------------


def _install(monkeypatch: pytest.MonkeyPatch, cursor: FakePgCursor) -> None:
    install_fake_pg(monkeypatch, cursor)
    monkeypatch.setattr(catalogs, "get_database_url", lambda: "postgresql://fake")


def _seed_skill(cursor: FakePgCursor, slug: str, name: str, uids: list[str]) -> None:
    cursor.skills[slug] = name
    for uid in uids:
        cursor.user_skills.setdefault(uid, set()).add(slug)


def test_delete_skill_cascades_assignments(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    _seed_skill(cursor, "go", "Go", ["uid-a", "uid-b"])
    _seed_skill(cursor, "vue", "Vue", ["uid-a"])

    response = catalogs.delete_skill("go")

    assert response.data == {"deleted": "go", "assignmentsRemoved": 2}
    assert "go" not in cursor.skills
    assert cursor.user_skills["uid-a"] == {"vue"}
    assert "uid-b" not in cursor.user_skills


def test_delete_skill_404_when_unknown(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)

    with pytest.raises(HTTPException) as exc:
        catalogs.delete_skill("ghost")

    assert exc.value.status_code == 404


def test_delete_skill_503_without_postgres(monkeypatch: pytest.MonkeyPatch):
    cursor = FakePgCursor()
    _install(monkeypatch, cursor)
    monkeypatch.setattr(catalogs, "get_database_url", lambda: None)

    with pytest.raises(HTTPException) as exc:
        catalogs.delete_skill("go")

    assert exc.value.status_code == 503


# ---------------------------------------------------------------------------
# DELETE /mcp/servers/{server_id} (issue #596)
# ---------------------------------------------------------------------------


def test_delete_mcp_server_cascades_sessions():
    app = create_app()
    with TestClient(app) as client:
        client.post("/api/v1/mcp/servers", json={"id": "srv-1", "name": "orders", "tools": ["t1"]})
        client.post("/api/v1/mcp/sessions", json={"id": "sess-1", "clientName": "web", "server": "orders"})
        client.post("/api/v1/mcp/sessions", json={"id": "sess-2", "clientName": "cli", "server": "srv-1"})
        client.post("/api/v1/mcp/sessions", json={"id": "sess-3", "clientName": "ui", "server": "other"})

        resp = client.request("DELETE", "/api/v1/mcp/servers/srv-1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["error"] is None
        assert body["data"] == {"id": "srv-1", "sessionsRemoved": "2"}

        servers = client.get("/api/v1/mcp/servers").json()["data"]
        assert "srv-1" not in [server["id"] for server in servers]
        sessions = client.get("/api/v1/mcp/sessions").json()["data"]
        assert [session["id"] for session in sessions] == ["sess-3"]


def test_delete_mcp_server_404_when_unknown():
    app = create_app()
    with TestClient(app) as client:
        resp = client.request("DELETE", "/api/v1/mcp/servers/ghost")

        assert resp.status_code == 404
        assert resp.json()["detail"] == "Server ghost not found"


# ---------------------------------------------------------------------------
# DELETE /chat/conversations/{conversation_id} (issue #596)
# ---------------------------------------------------------------------------


def _conversation(cid: str, participants: list[str]) -> dict[str, Any]:
    return {
        "id": cid,
        "title": None,
        "type": "direct",
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
        "reactions": [],
        "created_at": "2026-10-01T00:01:00+00:00",
    }


class FakeChatRepository:
    def __init__(self) -> None:
        self.conversations: dict[str, dict[str, Any]] = {
            CONV_ID: _conversation(CONV_ID, ["alice", "bob"]),
        }
        self.messages: list[dict[str, Any]] = [_message(CONV_ID, "alice", "hola", "m1")]
        self.degraded = False

    def _guard(self, action: str) -> None:
        if self.degraded:
            raise ChatStoreError(f"{action} unavailable")

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        self._guard("get")
        return self.conversations.get(conversation_id)

    async def delete_conversation(self, conversation_id: str) -> bool:
        self._guard("delete")
        existed = self.conversations.pop(conversation_id, None) is not None
        if existed:
            self.messages[:] = [m for m in self.messages if m["conversation_id"] != conversation_id]
        return existed


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
    app.state.chat_repository = repository
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, repo=repository)


def test_delete_conversation_owner_removes_messages(chat_env: SimpleNamespace):
    resp = chat_env.client.request(
        "DELETE", f"/api/v1/chat/conversations/{CONV_ID}", headers=_headers("alice")
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"] == {"deleted": CONV_ID}
    assert chat_env.repo.conversations == {}
    assert chat_env.repo.messages == []


def test_delete_conversation_404_for_stranger_unknown_and_invalid(chat_env: SimpleNamespace):
    resp = chat_env.client.request(
        "DELETE", f"/api/v1/chat/conversations/{CONV_ID}", headers=_headers("carol")
    )
    assert resp.status_code == 404

    resp = chat_env.client.request(
        "DELETE", f"/api/v1/chat/conversations/{UNKNOWN_CONV_ID}", headers=_headers("alice")
    )
    assert resp.status_code == 404

    resp = chat_env.client.request(
        "DELETE", "/api/v1/chat/conversations/not-an-objectid", headers=_headers("alice")
    )
    assert resp.status_code == 404

    assert CONV_ID in chat_env.repo.conversations
    assert len(chat_env.repo.messages) == 1


def test_delete_conversation_requires_identity(chat_env: SimpleNamespace):
    resp = chat_env.client.request("DELETE", f"/api/v1/chat/conversations/{CONV_ID}")

    assert resp.status_code == 401
    assert CONV_ID in chat_env.repo.conversations


def test_delete_conversation_503_when_degraded(chat_env: SimpleNamespace):
    chat_env.repo.degraded = True

    resp = chat_env.client.request(
        "DELETE", f"/api/v1/chat/conversations/{CONV_ID}", headers=_headers("alice")
    )

    assert resp.status_code == 503
    assert CONV_ID in chat_env.repo.conversations


def test_delete_conversation_503_without_store(monkeypatch: pytest.MonkeyPatch):
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

    with TestClient(app) as client:
        resp = client.request(
            "DELETE", f"/api/v1/chat/conversations/{CONV_ID}", headers=_headers("alice")
        )

    assert resp.status_code == 503
