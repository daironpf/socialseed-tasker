"""Realtime SSE endpoints for agent log streaming and issue presence (issue #517).

Provides:
- ``GET  /issues/{id}/agent-logs``          — buffered agent log history
- ``POST /issues/{id}/agent-logs``          — append + broadcast a log entry
- ``GET  /issues/{id}/agent-logs/stream``   — SSE stream (replay + live + heartbeat)
- ``GET  /issues/{id}/presence``            — current viewers (poll fallback)
- ``POST /issues/{id}/presence``            — join / heartbeat a viewer
- ``POST /issues/{id}/presence/leave``      — remove a viewer
- ``GET  /issues/{id}/presence/stream``     — SSE stream of viewer snapshots
- ``GET  /issues/{id}/github-sync/stream``  — SSE stream of GitHub sync events (issue #522)
- ``GET  /issues/stream``                   — SSE stream of issue flag changes (issue #530)

The ``/issues/stream`` route itself is registered in issues.py so that it wins
over ``GET /issues/{issue_id}``.

State lives in an in-process :class:`RealtimeHub` stored on ``app.state.realtime_hub``.
The hub also fans out ``notification_created`` events per ``user_id`` for the
``/notifications/stream`` SSE endpoint (issue #550).
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

realtime_router = APIRouter()

LOG_BUFFER_SIZE = 200
HEARTBEAT_SECONDS = 15.0
PRESENCE_TTL_MS = 90_000
#: Subscriber topics that mirror system-channel notifications (issue #550).
GLOBAL_NOTIFICATION_TOPICS: tuple[str, ...] = ("global", "system")

_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


def _sse(event: str, data: Any) -> str:
    """Format a Server-Sent Event frame."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _hub(request: Request) -> RealtimeHub:
    hub = getattr(request.app.state, "realtime_hub", None)
    if hub is None:
        hub = RealtimeHub()
        request.app.state.realtime_hub = hub
    return hub


def publish_github_sync(app: Any, issue_id: str, payload: dict[str, Any]) -> None:
    """Broadcast a GitHub sync event when a stream hub already exists."""
    hub = getattr(app.state, "realtime_hub", None)
    if hub is not None:
        hub.publish_sync(issue_id, payload)


def publish_issue_update(app: Any, issue_id: str, payload: dict[str, Any]) -> None:
    """Broadcast an issue flag change when a stream hub already exists (issue #530)."""
    hub = getattr(app.state, "realtime_hub", None)
    if hub is not None:
        hub.publish_issue_update({"issue_id": issue_id, **payload})


class RealtimeHub:
    """In-process pub/sub hub: per-issue log buffers, presence registries and
    per-user notification fan-out (issue #550).

    All methods are synchronous and run on the event loop, so a
    ``subscribe_*`` call is atomic with respect to publishers.
    """

    def __init__(self) -> None:
        self._logs: dict[str, list[dict[str, Any]]] = {}
        self._log_subs: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._presence: dict[str, dict[str, dict[str, Any]]] = {}
        self._presence_subs: dict[str, list[asyncio.Queue[list[dict[str, Any]]]]] = {}
        self._sync_subs: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._notif_subs: dict[str, list[asyncio.Queue[dict[str, Any]]]] = {}
        self._issue_subs: list[asyncio.Queue[dict[str, Any]]] = []

    # --------------------------------------------------------- issue updates

    def publish_issue_update(self, payload: dict[str, Any]) -> None:
        """Broadcast an issue flag change (agent_working) to all subscribers."""
        entry = {"event": "issue-updated", "data": payload}
        for queue in list(self._issue_subs):
            queue.put_nowait(entry)

    def subscribe_issues(self) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._issue_subs.append(queue)
        return queue

    def unsubscribe_issues(self, queue: asyncio.Queue[dict[str, Any]]) -> None:
        if queue in self._issue_subs:
            self._issue_subs.remove(queue)

    # ---------------------------------------------------------- github sync

    def publish_sync(self, issue_id: str, payload: dict[str, Any]) -> None:
        entry = {"event": "sync", "data": {"issue_id": issue_id, **payload}}
        for queue in self._sync_subs.get(issue_id, []):
            queue.put_nowait(entry)

    def subscribe_sync(self, issue_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._sync_subs.setdefault(issue_id, []).append(queue)
        return queue

    def unsubscribe_sync(self, issue_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subs = self._sync_subs.get(issue_id, [])
        if queue in subs:
            subs.remove(queue)

    # ------------------------------------------------------- notifications

    def publish_notification(self, user_id: str, payload: dict[str, Any]) -> None:
        """Deliver a ``notification_created`` event to the target user's streams.

        System-channel notifications (welcome, ...) are additionally mirrored
        to the global subscriber topics ``global``/``system`` so channel-wide
        dashboards see them (issue #550); every other channel stays strictly
        private to ``user_id``.
        """
        entry = {"event": "notification_created", "data": payload}
        topics = [user_id]
        if str(payload.get("channel", "")).lower() == "system":
            topics.extend(GLOBAL_NOTIFICATION_TOPICS)
        for topic in dict.fromkeys(topics):
            for queue in list(self._notif_subs.get(topic, [])):
                queue.put_nowait(entry)

    def subscribe_notifications(self, user_id: str) -> asyncio.Queue[dict[str, Any]]:
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._notif_subs.setdefault(user_id, []).append(queue)
        return queue

    def unsubscribe_notifications(self, user_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subs = self._notif_subs.get(user_id, [])
        if queue in subs:
            subs.remove(queue)

    # ------------------------------------------------------------------ logs

    def append_log(self, issue_id: str, log: dict[str, Any]) -> dict[str, Any]:
        entry: dict[str, Any] = {
            "id": str(uuid.uuid4()),
            "timestamp": log.get("timestamp")
            or time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "type": log.get("type", "progress"),
            "content_markdown": log.get("content_markdown", ""),
        }
        if log.get("agent"):
            entry["agent"] = log["agent"]
        buffer = self._logs.setdefault(issue_id, [])
        buffer.append(entry)
        if len(buffer) > LOG_BUFFER_SIZE:
            del buffer[:-LOG_BUFFER_SIZE]
        for queue in self._log_subs.get(issue_id, []):
            queue.put_nowait({"event": "log", "data": entry})
        return entry

    def replay_logs(self, issue_id: str) -> list[dict[str, Any]]:
        return list(self._logs.get(issue_id, []))

    def subscribe_logs(self, issue_id: str) -> tuple[asyncio.Queue[dict[str, Any]], list[dict[str, Any]]]:
        """Atomically snapshot the buffer and register a live subscriber."""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        snapshot = list(self._logs.get(issue_id, []))
        self._log_subs.setdefault(issue_id, []).append(queue)
        return queue, snapshot

    def unsubscribe_logs(self, issue_id: str, queue: asyncio.Queue[dict[str, Any]]) -> None:
        subs = self._log_subs.get(issue_id, [])
        if queue in subs:
            subs.remove(queue)

    # -------------------------------------------------------------- presence

    def upsert_viewer(self, issue_id: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        registry = self._presence.setdefault(issue_id, {})
        user_id = str(payload.get("user_id") or uuid.uuid4())
        viewer: dict[str, Any] = {
            "id": user_id,
            "username": payload.get("username") or user_id,
            "avatar": payload.get("avatar") or "\U0001f464",
            "type": payload.get("type") or "human",
            "lastSeen": int(time.time() * 1000),
        }
        if payload.get("viewing_field"):
            viewer["viewingField"] = payload["viewing_field"]
        if "is_typing" in payload:
            viewer["isTyping"] = bool(payload["is_typing"])
        if payload.get("typing_message"):
            viewer["typingMessage"] = payload["typing_message"]
        registry[user_id] = viewer
        viewers = self.viewers(issue_id)
        self._broadcast_presence(issue_id, viewers)
        return viewers

    def remove_viewer(self, issue_id: str, user_id: str) -> list[dict[str, Any]]:
        registry = self._presence.get(issue_id, {})
        registry.pop(str(user_id), None)
        viewers = self.viewers(issue_id)
        self._broadcast_presence(issue_id, viewers)
        return viewers

    def viewers(self, issue_id: str) -> list[dict[str, Any]]:
        registry = self._presence.get(issue_id, {})
        now = time.time() * 1000
        stale = [uid for uid, v in registry.items() if now - v.get("lastSeen", 0) > PRESENCE_TTL_MS]
        for uid in stale:
            del registry[uid]
        return list(registry.values())

    def tick_presence(self, issue_id: str) -> None:
        """Prune stale viewers and broadcast when the snapshot changed."""
        registry = self._presence.get(issue_id, {})
        before = list(registry.values())
        now = time.time() * 1000
        stale = [uid for uid, v in registry.items() if now - v.get("lastSeen", 0) > PRESENCE_TTL_MS]
        if not stale:
            return
        for uid in stale:
            del registry[uid]
        after = list(registry.values())
        if after != before:
            self._broadcast_presence(issue_id, after)

    def subscribe_presence(self, issue_id: str) -> tuple[asyncio.Queue[list[dict[str, Any]]], list[dict[str, Any]]]:
        queue: asyncio.Queue[list[dict[str, Any]]] = asyncio.Queue()
        snapshot = self.viewers(issue_id)
        self._presence_subs.setdefault(issue_id, []).append(queue)
        return queue, snapshot

    def unsubscribe_presence(self, issue_id: str, queue: asyncio.Queue[list[dict[str, Any]]]) -> None:
        subs = self._presence_subs.get(issue_id, [])
        if queue in subs:
            subs.remove(queue)

    def _broadcast_presence(self, issue_id: str, viewers: list[dict[str, Any]]) -> None:
        for queue in self._presence_subs.get(issue_id, []):
            queue.put_nowait(viewers)


# --------------------------------------------------------------------- logs


@realtime_router.get("/issues/{issue_id}/agent-logs")
async def get_agent_logs(issue_id: str, request: Request) -> dict[str, Any]:
    hub = _hub(request)
    return {"data": {"issue_id": issue_id, "logs": hub.replay_logs(issue_id)}}


@realtime_router.post("/issues/{issue_id}/agent-logs")
async def publish_agent_log(issue_id: str, payload: dict[str, Any], request: Request) -> dict[str, Any]:
    hub = _hub(request)
    entry = hub.append_log(issue_id, payload)
    return {"data": entry}


@realtime_router.get("/issues/{issue_id}/agent-logs/stream")
async def stream_agent_logs(issue_id: str, request: Request) -> StreamingResponse:
    hub = _hub(request)
    queue, snapshot = hub.subscribe_logs(issue_id)

    async def generate():
        try:
            yield _sse(
                "connected",
                {"issue_id": issue_id, "replayed": len(snapshot)},
            )
            for entry in snapshot:
                yield _sse("log", entry)
            while True:
                if await request.is_disconnected():
                    return
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    yield _sse("ping", {"ts": int(time.time() * 1000)})
                    continue
                yield _sse(item["event"], item["data"])
        finally:
            hub.unsubscribe_logs(issue_id, queue)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)


# --------------------------------------------------------------- presence


@realtime_router.get("/issues/{issue_id}/presence")
async def get_presence(issue_id: str, request: Request) -> dict[str, Any]:
    hub = _hub(request)
    return {"data": {"viewers": hub.viewers(issue_id)}}


@realtime_router.post("/issues/{issue_id}/presence")
async def upsert_presence(issue_id: str, payload: dict[str, Any], request: Request) -> dict[str, Any]:
    hub = _hub(request)
    return {"data": {"viewers": hub.upsert_viewer(issue_id, payload)}}


@realtime_router.post("/issues/{issue_id}/presence/leave")
async def leave_presence(issue_id: str, payload: dict[str, Any], request: Request) -> dict[str, Any]:
    hub = _hub(request)
    return {"data": {"viewers": hub.remove_viewer(issue_id, str(payload.get("user_id", "")))}}


@realtime_router.get("/issues/{issue_id}/presence/stream")
async def stream_presence(issue_id: str, request: Request) -> StreamingResponse:
    hub = _hub(request)
    queue, snapshot = hub.subscribe_presence(issue_id)

    async def generate():
        try:
            yield _sse("connected", {"issue_id": issue_id})
            yield _sse("viewers", {"viewers": snapshot})
            while True:
                if await request.is_disconnected():
                    return
                try:
                    viewers = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    hub.tick_presence(issue_id)
                    yield _sse("ping", {"ts": int(time.time() * 1000)})
                    continue
                yield _sse("viewers", {"viewers": viewers})
        finally:
            hub.unsubscribe_presence(issue_id, queue)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)


# ----------------------------------------------------------- github sync


@realtime_router.get("/issues/{issue_id}/github-sync/stream")
async def stream_github_sync(issue_id: str, request: Request) -> StreamingResponse:
    """Live stream of GitHub sync events (webhook updates, conflicts) for one issue."""
    hub = _hub(request)
    queue = hub.subscribe_sync(issue_id)

    async def generate() -> AsyncGenerator[str, None]:
        try:
            yield _sse("connected", {"issue_id": issue_id})
            while True:
                if await request.is_disconnected():
                    return
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    yield _sse("ping", {"ts": int(time.time() * 1000)})
                    continue
                yield _sse(item["event"], item["data"])
        finally:
            hub.unsubscribe_sync(issue_id, queue)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)


# ----------------------------------------------------------- issue updates


def issue_updates_stream(request: Request) -> StreamingResponse:
    """SSE stream of issue flag changes (issue #530).

    The route lives in issues.py as ``GET /issues/stream`` so it is registered
    before ``GET /issues/{issue_id}`` and is not shadowed by it.
    """
    hub = _hub(request)
    queue = hub.subscribe_issues()

    async def generate() -> AsyncGenerator[str, None]:
        try:
            yield _sse("connected", {"scope": "issues"})
            while True:
                if await request.is_disconnected():
                    return
                try:
                    item = await asyncio.wait_for(queue.get(), timeout=HEARTBEAT_SECONDS)
                except asyncio.TimeoutError:
                    yield _sse("ping", {"ts": int(time.time() * 1000)})
                    continue
                yield _sse(item["event"], item["data"])
        finally:
            hub.unsubscribe_issues(queue)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)
