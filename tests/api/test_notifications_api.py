"""Notifications REST API tests (issue #548).

Runs over TestClient with an in-memory fake repository: APIResponse envelope
(camelCase), strict per-user isolation from the JWT, 404 semantics for
foreign/unknown ids, query validation and 503 degradation.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.mongo.notification_repository import NotificationStoreError
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.models.notification import (
    Notification,
    NotificationSeverity,
    NotificationType,
)

ALICE_HITL = "64c1000000000000000000a1"  # unread, requires action
ALICE_MENTION = "64c1000000000000000000a2"  # read
ALICE_SLA = "64c1000000000000000000a3"  # unread, newest
BOB_FAILURE = "64c1000000000000000000b1"
UNKNOWN_ID = "64c1000000000000000000f0"  # valid ObjectId, absent

BASE = datetime(2026, 10, 1, 0, 0, tzinfo=timezone.utc)


def _note(
    note_id: str,
    user_id: str,
    note_type: NotificationType,
    *,
    minutes: int = 0,
    read: bool = False,
    channel: str = "hitl",
    severity: NotificationSeverity = NotificationSeverity.INFO,
    **extra: Any,
) -> Notification:
    payload: dict[str, Any] = {
        "id": note_id,
        "user_id": user_id,
        "type": note_type,
        "severity": severity,
        "title": f"title-{note_id}",
        "message": f"message-{note_id}",
        "read": read,
        "channel": channel,
        "created_at": BASE + timedelta(minutes=minutes),
    }
    payload.update(extra)
    return Notification.model_validate(payload)


class FakeNotificationRepository:
    def __init__(self) -> None:
        self.notes: dict[str, Notification] = {
            ALICE_HITL: _note(
                ALICE_HITL,
                "alice",
                NotificationType.HITL,
                minutes=1,
                channel="hitl",
                severity=NotificationSeverity.WARNING,
                requires_action=True,
                hitl_request_id="req-1",
                link_to="/issues/1",
            ),
            ALICE_MENTION: _note(
                ALICE_MENTION, "alice", NotificationType.MENTION, minutes=2,
                read=True, channel="mention",
            ),
            ALICE_SLA: _note(
                ALICE_SLA, "alice", NotificationType.SLA, minutes=3,
                channel="sla", severity=NotificationSeverity.EMERGENCY,
            ),
            BOB_FAILURE: _note(
                BOB_FAILURE, "bob", NotificationType.AGENT_FAILURE, minutes=4,
                channel="agent_failure",
            ),
        }
        self.degraded = False
        self.calls: list[tuple[Any, ...]] = []

    def _guard(self, action: str) -> None:
        if self.degraded:
            raise NotificationStoreError(f"{action} unavailable")

    async def list_for_user(
        self,
        user_id: str,
        *,
        read: bool | None = None,
        notification_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        self._guard("list")
        self.calls.append(("list", user_id, read, notification_type, limit, offset))
        matched = [n for n in self.notes.values() if n.user_id == user_id]
        if read is not None:
            matched = [n for n in matched if n.read is read]
        if notification_type:
            matched = [n for n in matched if n.type.value == notification_type]
        matched.sort(key=lambda n: n.created_at, reverse=True)
        return matched[offset : offset + limit], len(matched)

    async def mark_read(self, notification_id: str, user_id: str) -> Notification | None:
        self._guard("mark_read")
        self.calls.append(("mark_read", notification_id, user_id))
        note = self.notes.get(notification_id)
        if note is None or note.user_id != user_id:
            return None
        updated = note.model_copy(update={"read": True})
        self.notes[notification_id] = updated
        return updated

    async def mark_all_read(self, user_id: str) -> int:
        self._guard("mark_all_read")
        count = 0
        for note_id, note in list(self.notes.items()):
            if note.user_id == user_id and not note.read:
                self.notes[note_id] = note.model_copy(update={"read": True})
                count += 1
        return count

    async def delete(self, notification_id: str, user_id: str) -> bool:
        self._guard("delete")
        note = self.notes.get(notification_id)
        if note is None or note.user_id != user_id:
            return False
        del self.notes[notification_id]
        return True

    async def clear_all(self, user_id: str, only_read: bool = False) -> int:
        self._guard("clear_all")
        doomed = [
            note_id
            for note_id, note in self.notes.items()
            if note.user_id == user_id and (note.read if only_read else True)
        ]
        for note_id in doomed:
            del self.notes[note_id]
        return len(doomed)


def _headers(user_id: str) -> dict[str, str]:
    tokens = issue_tokens({"id": user_id, "username": user_id})
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest.fixture()
def notif_env(monkeypatch: pytest.MonkeyPatch) -> Any:
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
    repository = FakeNotificationRepository()
    app.state.notification_repository = repository
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, repo=repository)


def test_endpoints_require_identity(notif_env: SimpleNamespace) -> None:
    assert notif_env.client.get("/api/v1/notifications").status_code == 401
    assert notif_env.client.post("/api/v1/notifications/mark-all-read").status_code == 401
    assert notif_env.client.post("/api/v1/notifications/clear-all").status_code == 401
    assert (
        notif_env.client.patch(f"/api/v1/notifications/{ALICE_HITL}/read").status_code == 401
    )
    assert notif_env.client.delete(f"/api/v1/notifications/{ALICE_HITL}").status_code == 401


def test_list_envelope_wire_and_user_isolation(notif_env: SimpleNamespace) -> None:
    resp = notif_env.client.get("/api/v1/notifications", headers=_headers("alice"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    items = body["data"]
    assert [n["id"] for n in items] == [ALICE_SLA, ALICE_MENTION, ALICE_HITL]
    newest = items[0]
    assert newest["userId"] == "alice"
    assert newest["category"] == "sla"
    assert newest["severity"] == "EMERGENCY"
    assert newest["requiresAction"] is False
    assert newest["createdAt"].startswith("2026-10-01T00:0")
    assert "user_id" not in newest
    assert "created_at" not in newest
    assert "requires_action" not in newest
    hitl = next(n for n in items if n["id"] == ALICE_HITL)
    assert hitl["requiresAction"] is True
    assert hitl["hitlRequestId"] == "req-1"
    assert hitl["linkTo"] == "/issues/1"
    pagination = body["meta"]["pagination"]
    assert pagination["total"] == 3
    assert pagination["limit"] == 50
    assert pagination["page"] == 1
    assert pagination["has_next"] is False
    assert pagination["has_prev"] is False
    assert ("list", "alice", None, None, 50, 0) in notif_env.repo.calls

    resp_bob = notif_env.client.get("/api/v1/notifications", headers=_headers("bob"))
    assert resp_bob.status_code == 200
    bob_items = resp_bob.json()["data"]
    assert [n["id"] for n in bob_items] == [BOB_FAILURE]
    assert bob_items[0]["category"] == "agent_failure"


def test_list_filters_and_query_validation(notif_env: SimpleNamespace) -> None:
    resp = notif_env.client.get("/api/v1/notifications?read=true", headers=_headers("alice"))
    assert resp.status_code == 200
    body = resp.json()
    assert [n["id"] for n in body["data"]] == [ALICE_MENTION]
    assert body["meta"]["pagination"]["total"] == 1

    resp = notif_env.client.get("/api/v1/notifications?category=hitl", headers=_headers("alice"))
    assert resp.status_code == 200
    assert [n["id"] for n in resp.json()["data"]] == [ALICE_HITL]

    resp = notif_env.client.get(
        "/api/v1/notifications?category=mention&read=true", headers=_headers("alice")
    )
    assert resp.status_code == 200
    assert [n["id"] for n in resp.json()["data"]] == [ALICE_MENTION]

    resp = notif_env.client.get("/api/v1/notifications?category=nope", headers=_headers("alice"))
    assert resp.status_code == 400

    assert (
        notif_env.client.get("/api/v1/notifications?limit=0", headers=_headers("alice")).status_code
        == 422
    )
    assert (
        notif_env.client.get("/api/v1/notifications?read=maybe", headers=_headers("alice")).status_code
        == 422
    )

    resp = notif_env.client.get(
        "/api/v1/notifications?limit=1&offset=1", headers=_headers("alice")
    )
    assert resp.status_code == 200
    body = resp.json()
    assert [n["id"] for n in body["data"]] == [ALICE_MENTION]
    pagination = body["meta"]["pagination"]
    assert pagination["page"] == 2
    assert pagination["total"] == 3
    assert pagination["has_prev"] is True
    assert pagination["has_next"] is True

    resp = notif_env.client.get("/api/v1/notifications?offset=99", headers=_headers("alice"))
    assert resp.status_code == 200
    assert resp.json()["data"] == []
    assert resp.json()["meta"]["pagination"]["page"] == 2


def test_mark_read_ownership_and_404(notif_env: SimpleNamespace) -> None:
    resp = notif_env.client.patch(
        f"/api/v1/notifications/{ALICE_SLA}/read", headers=_headers("bob")
    )
    assert resp.status_code == 404
    assert notif_env.repo.notes[ALICE_SLA].read is False

    resp = notif_env.client.patch(
        f"/api/v1/notifications/{UNKNOWN_ID}/read", headers=_headers("alice")
    )
    assert resp.status_code == 404

    resp = notif_env.client.patch(
        f"/api/v1/notifications/{ALICE_SLA}/read", headers=_headers("alice")
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"]["id"] == ALICE_SLA
    assert body["data"]["read"] is True

    resp = notif_env.client.patch(
        f"/api/v1/notifications/{ALICE_SLA}/read", headers=_headers("alice")
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["read"] is True
    assert ("mark_read", ALICE_SLA, "bob") in notif_env.repo.calls


def test_mark_all_read_is_scoped_to_caller(notif_env: SimpleNamespace) -> None:
    resp = notif_env.client.post("/api/v1/notifications/mark-all-read", headers=_headers("alice"))
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"] == {"matchedCount": 2}
    assert notif_env.repo.notes[ALICE_HITL].read is True
    assert notif_env.repo.notes[ALICE_SLA].read is True
    assert notif_env.repo.notes[BOB_FAILURE].read is False

    resp = notif_env.client.post("/api/v1/notifications/mark-all-read", headers=_headers("alice"))
    assert resp.json()["data"] == {"matchedCount": 0}

    resp = notif_env.client.get(
        "/api/v1/notifications?read=true", headers=_headers("alice")
    )
    assert resp.json()["meta"]["pagination"]["total"] == 3


def test_delete_ownership_and_404(notif_env: SimpleNamespace) -> None:
    resp = notif_env.client.delete(
        f"/api/v1/notifications/{ALICE_MENTION}", headers=_headers("bob")
    )
    assert resp.status_code == 404
    assert ALICE_MENTION in notif_env.repo.notes

    resp = notif_env.client.delete(
        f"/api/v1/notifications/{UNKNOWN_ID}", headers=_headers("alice")
    )
    assert resp.status_code == 404

    resp = notif_env.client.delete(
        f"/api/v1/notifications/{ALICE_MENTION}", headers=_headers("alice")
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"] == {"id": ALICE_MENTION, "deleted": True}
    assert ALICE_MENTION not in notif_env.repo.notes

    resp = notif_env.client.get("/api/v1/notifications", headers=_headers("alice"))
    assert resp.json()["meta"]["pagination"]["total"] == 2


def test_clear_all_scope_and_only_read_param(notif_env: SimpleNamespace) -> None:
    resp = notif_env.client.post(
        "/api/v1/notifications/clear-all?onlyRead=true", headers=_headers("alice")
    )
    assert resp.status_code == 200
    assert resp.json()["data"] == {"deletedCount": 1}
    assert ALICE_MENTION not in notif_env.repo.notes
    assert ALICE_HITL in notif_env.repo.notes
    assert BOB_FAILURE in notif_env.repo.notes

    resp = notif_env.client.post("/api/v1/notifications/clear-all", headers=_headers("alice"))
    assert resp.json()["data"] == {"deletedCount": 2}
    assert [n.user_id for n in notif_env.repo.notes.values()] == ["bob"]
    assert BOB_FAILURE in notif_env.repo.notes


def test_store_degrades_to_503(notif_env: SimpleNamespace) -> None:
    notif_env.repo.degraded = True
    resp = notif_env.client.get("/api/v1/notifications", headers=_headers("alice"))
    assert resp.status_code == 503
    resp = notif_env.client.post("/api/v1/notifications/mark-all-read", headers=_headers("alice"))
    assert resp.status_code == 503
    resp = notif_env.client.post("/api/v1/notifications/clear-all", headers=_headers("alice"))
    assert resp.status_code == 503
    resp = notif_env.client.patch(
        f"/api/v1/notifications/{ALICE_HITL}/read", headers=_headers("alice")
    )
    assert resp.status_code == 503
    resp = notif_env.client.delete(f"/api/v1/notifications/{ALICE_HITL}", headers=_headers("alice"))
    assert resp.status_code == 503
