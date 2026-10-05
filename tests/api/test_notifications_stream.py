"""Realtime notification SSE stream tests (issue #550).

The handler is invoked directly as ``stream_notifications(Request(scope, receive))``
(pattern of #524/#530) because ``TestClient.stream`` hangs on every SSE endpoint
in this environment; only the unauthenticated 401 travels through TestClient
(that response terminates before streaming starts). Covers: auth rejection,
``connected`` + snapshot wire, reactive ``notification_created`` delivery,
per-user isolation with global system-channel mirroring, best-effort snapshot
degradation and subscriber cleanup on close/disconnect.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient

from socialseed_tasker.auth.tokens import issue_tokens
from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.infrastructure.web_api.routers import (
    notifications as notifications_module,
)
from socialseed_tasker.infrastructure.web_api.routers.realtime import RealtimeHub
from socialseed_tasker.models.notification import (
    Notification,
    NotificationSeverity,
    NotificationType,
)
from test_notifications_api import FakeNotificationRepository

ALICE_HITL = "64c1000000000000000000a1"
ALICE_SLA = "64c1000000000000000000a3"
BOB_FAILURE = "64c1000000000000000000b1"
NEW_MENTION = "64c1000000000000000000c1"


def _note(
    note_id: str,
    user_id: str,
    note_type: NotificationType,
    *,
    channel: str,
    **extra: Any,
) -> Notification:
    payload: dict[str, Any] = {
        "id": note_id,
        "user_id": user_id,
        "type": note_type,
        "severity": NotificationSeverity.INFO,
        "title": f"title-{note_id}",
        "message": f"message-{note_id}",
        "channel": channel,
    }
    payload.update(extra)
    return Notification.model_validate(payload)


def _app(hub: RealtimeHub, repository: Any | None) -> Any:
    state = SimpleNamespace(realtime_hub=hub)
    if repository is not None:
        state.notification_repository = repository
    return SimpleNamespace(state=state)


def _scope(user_id: str | None, app: Any) -> dict[str, Any]:
    headers: list[tuple[bytes, bytes]] = []
    if user_id is not None:
        tokens = issue_tokens({"id": user_id, "username": user_id})
        headers.append(
            (b"authorization", f"Bearer {tokens['access_token']}".encode("ascii"))
        )
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/v1/notifications/stream",
        "raw_path": b"/api/v1/notifications/stream",
        "query_string": b"",
        "root_path": "",
        "headers": headers,
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "app": app,
        "router": getattr(app, "router", None),
    }


async def _receive_alive() -> dict[str, Any]:
    # Non-blocking poll result: keep the stream loop running (the request
    # is still connected, so is_disconnected() must answer False).
    return {"type": "http.request", "body": b"", "more_body": False}


async def _receive_gone() -> dict[str, Any]:
    return {"type": "http.disconnect"}


async def _first_frame(resp: Any) -> str:
    async for chunk in resp.body_iterator:
        return chunk
    raise AssertionError("stream produced no frames")


@pytest.fixture()
def stream_env(monkeypatch: pytest.MonkeyPatch) -> Any:
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
    app.state.notification_repository = FakeNotificationRepository()
    with TestClient(app) as client:
        yield SimpleNamespace(client=client, app=app)


def test_stream_route_registered_and_requires_identity(stream_env: Any) -> None:
    paths = [getattr(route, "path", None) for route in stream_env.app.routes]
    assert "/api/v1/notifications/stream" in paths
    # Unauthenticated request answers before any streaming starts (the SSE
    # response itself would block TestClient, hence only the 401 case here).
    resp = stream_env.client.get("/api/v1/notifications/stream")
    assert resp.status_code == 401


async def test_stream_handler_rejects_caller_without_token() -> None:
    app = _app(RealtimeHub(), FakeNotificationRepository())
    with pytest.raises(HTTPException) as excinfo:
        await notifications_module.stream_notifications(
            Request(_scope(None, app), _receive_alive)
        )
    assert excinfo.value.status_code == 401


async def test_stream_sends_connected_snapshot_and_cleans_up() -> None:
    hub = RealtimeHub()
    app = _app(hub, FakeNotificationRepository())
    resp = await notifications_module.stream_notifications(
        Request(_scope("alice", app), _receive_alive)
    )
    assert resp.media_type == "text/event-stream"
    assert "text/event-stream" in resp.headers["content-type"]
    assert resp.headers["x-accel-buffering"] == "no"
    assert "no-cache" in resp.headers["cache-control"]

    text = await _first_frame(resp)
    assert text.startswith("event: connected\n")
    data = json.loads(text.split("data: ", 1)[1])
    assert data["userId"] == "alice"
    # Newest first, own notifications only (bob's failure never leaks in).
    assert [item["id"] for item in data["snapshot"]] == [
        ALICE_SLA,
        "64c1000000000000000000a2",
        ALICE_HITL,
    ]
    assert BOB_FAILURE not in text
    newest = data["snapshot"][0]
    assert newest["category"] == "sla"
    assert newest["severity"] == "EMERGENCY"
    assert "created_at" not in newest

    assert len(hub._notif_subs.get("alice", [])) == 1
    await resp.body_iterator.aclose()
    assert not hub._notif_subs.get("alice")


async def test_stream_delivers_reactive_notification_to_target_only() -> None:
    hub = RealtimeHub()
    app = _app(hub, FakeNotificationRepository())
    alice = await notifications_module.stream_notifications(
        Request(_scope("alice", app), _receive_alive)
    )
    bob = await notifications_module.stream_notifications(
        Request(_scope("bob", app), _receive_alive)
    )
    alice_iter = alice.body_iterator
    bob_iter = bob.body_iterator
    await alice_iter.__anext__()
    await bob_iter.__anext__()
    assert len(hub._notif_subs.get("alice", [])) == 1
    assert len(hub._notif_subs.get("bob", [])) == 1

    note = _note(
        NEW_MENTION, "alice", NotificationType.MENTION, channel="mention"
    )
    notifications_module.emit_notification_created(app, note)

    frame = await alice_iter.__anext__()
    assert frame.startswith("event: notification_created\n")
    wire = json.loads(frame.split("data: ", 1)[1])
    assert wire["id"] == NEW_MENTION
    assert wire["userId"] == "alice"
    assert wire["category"] == "mention"
    assert "user_id" not in wire

    # Strict per-user fan-out: bob subscribed but the event was alice's.
    assert hub._notif_subs["bob"][0].empty()

    await alice_iter.aclose()
    await bob_iter.aclose()
    assert not hub._notif_subs.get("alice")
    assert not hub._notif_subs.get("bob")


async def test_stream_disconnect_terminates_and_unsubscribes() -> None:
    hub = RealtimeHub()
    app = _app(hub, FakeNotificationRepository())
    resp = await notifications_module.stream_notifications(
        Request(_scope("alice", app), _receive_gone)
    )
    frames = [frame async for frame in resp.body_iterator]
    assert len(frames) == 1
    assert frames[0].startswith("event: connected\n")
    assert not hub._notif_subs.get("alice")


async def test_stream_snapshot_degrades_to_empty() -> None:
    # Unreachable store (typed NotificationStoreError): the stream still
    # connects with snapshot [] so realtime is not lost with history.
    hub = RealtimeHub()
    repository = FakeNotificationRepository()
    repository.degraded = True
    app = _app(hub, repository)
    resp = await notifications_module.stream_notifications(
        Request(_scope("alice", app), _receive_alive)
    )
    text = await _first_frame(resp)
    assert text.startswith("event: connected\n")
    assert '"snapshot": []' in text
    await resp.body_iterator.aclose()
    assert not hub._notif_subs.get("alice")

    # Missing repository entirely: same best-effort degradation.
    hub_2 = RealtimeHub()
    resp_2 = await notifications_module.stream_notifications(
        Request(_scope("alice", _app(hub_2, None)), _receive_alive)
    )
    text_2 = await _first_frame(resp_2)
    assert '"snapshot": []' in text_2
    await resp_2.body_iterator.aclose()
    assert not hub_2._notif_subs.get("alice")


def test_hub_fanout_targets_destination_and_system_globals() -> None:
    hub = RealtimeHub()
    alice_queue = hub.subscribe_notifications("alice")
    bob_queue = hub.subscribe_notifications("bob")
    global_queue = hub.subscribe_notifications("global")
    system_queue = hub.subscribe_notifications("system")

    hub.publish_notification("alice", {"channel": "mention", "userId": "alice"})
    assert not alice_queue.empty()
    assert bob_queue.empty()
    assert global_queue.empty()
    assert system_queue.empty()
    entry = alice_queue.get_nowait()
    assert entry["event"] == "notification_created"
    assert entry["data"]["userId"] == "alice"

    # System channel mirrors to the global topics but never to other users.
    hub.publish_notification("bob", {"channel": "system", "userId": "bob"})
    assert not bob_queue.empty()
    assert not global_queue.empty()
    assert not system_queue.empty()
    assert alice_queue.empty()

    hub.unsubscribe_notifications("bob", bob_queue)
    assert bob_queue not in hub._notif_subs.get("bob", [])


def test_emit_without_hub_is_a_noop() -> None:
    app = SimpleNamespace(state=SimpleNamespace())
    notifications_module.emit_notification_created(
        app,
        _note("64c1000000000000000000c9", "alice", NotificationType.MENTION, channel="mention"),
    )


def test_emit_publishes_camelcase_wire_payload() -> None:
    hub = RealtimeHub()
    app = SimpleNamespace(state=SimpleNamespace(realtime_hub=hub))
    queue = hub.subscribe_notifications("alice")
    notifications_module.emit_notification_created(
        app,
        _note(
            "64c1000000000000000000c2",
            "alice",
            NotificationType.HITL,
            channel="hitl",
            requires_action=True,
            hitl_request_id="req-9",
        ),
    )
    entry = queue.get_nowait()
    assert entry["event"] == "notification_created"
    wire = entry["data"]
    assert wire["userId"] == "alice"
    assert wire["category"] == "hitl"
    assert wire["requiresAction"] is True
    assert wire["hitlRequestId"] == "req-9"
    assert "created_at" not in wire
    assert "requires_action" not in wire
