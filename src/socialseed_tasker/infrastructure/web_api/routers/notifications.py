"""REST notification endpoints: list, read state and cleanup — issue #548.

Endpoints under ``/api/v1/notifications/*`` return the shared ``APIResponse``
envelope (camelCase: ``createdAt``, ``requiresAction``, ``hitlRequestId``,
``linkTo``). The caller identity always comes from the request JWT (never
from the body) so one user can never read, mark or delete another user's
notifications — foreign/unknown ids answer 404 without leaking existence.
Persistence goes through the Mongo repository (#547) and degrades to a typed
503 when MongoDB is not configured or unreachable.

``GET /notifications/stream`` (issue #550) is the realtime companion: an SSE
stream of ``notification_created`` events for the JWT caller, fed by the
single publication point :func:`emit_notification_created` called from every
insertion path (#549 welcome seed; future create endpoints). Its identity
also accepts ``?access_token=`` because browser ``EventSource`` cannot send
headers (issue #551).
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from socialseed_tasker.auth.tokens import verify_access
from socialseed_tasker.infrastructure.mongo.notification_repository import (
    NotificationMongoRepository,
    NotificationStoreError,
)
from socialseed_tasker.infrastructure.web_api.routers.chat import _current_user
from socialseed_tasker.infrastructure.web_api.routers.realtime import (
    _SSE_HEADERS,
    HEARTBEAT_SECONDS,
    _hub,
    _sse,
)
from socialseed_tasker.infrastructure.web_api.schemas import (
    APIResponse,
    Meta,
    PaginationMeta,
)
from socialseed_tasker.models.notification import (
    FRONTEND_CATEGORIES,
    Notification,
)

notifications_router = APIRouter()
logger = logging.getLogger(__name__)

#: Notifications replayed in the ``connected`` frame of the SSE stream (#550).
_STREAM_SNAPSHOT_LIMIT = 50


def _repository(request: Request) -> NotificationMongoRepository:
    repository: NotificationMongoRepository | None = getattr(
        request.app.state, "notification_repository", None
    )
    if repository is None:
        raise HTTPException(status_code=503, detail="notifications store unavailable")
    return repository


def _store_error(exc: NotificationStoreError, action: str) -> HTTPException:
    logger.warning("notifications %s degraded: %s", action, exc)
    return HTTPException(status_code=503, detail="notifications store unavailable")


def _category_type(category: str | None) -> str | None:
    """Resolve a frontend category (`mention`, ...) to the stored enum value."""
    if not category:
        return None
    for note_type, name in FRONTEND_CATEGORIES.items():
        if name == category:
            return note_type.value
    raise ValueError(f"unknown notification category: {category}")


def _wire(note: Notification) -> dict[str, Any]:
    """Serialize a Notification to the camelCase wire contract consumed by #551."""
    wire: dict[str, Any] = {
        "id": note.id,
        "userId": note.user_id,
        "type": note.type.value,
        "category": note.category,
        "severity": note.severity.value,
        "title": note.title,
        "message": note.message,
        "read": note.read,
        "requiresAction": note.requires_action,
        "channel": note.channel,
        "createdAt": note.created_at.isoformat(),
    }
    if note.link_to is not None:
        wire["linkTo"] = note.link_to
    if note.hitl_request_id is not None:
        wire["hitlRequestId"] = note.hitl_request_id
    return wire


def emit_notification_created(app: Any, note: Notification) -> None:
    """Publish a freshly inserted notification to live streams (issue #550).

    The single publication point shared by every insertion path (#549 welcome
    seed, future create endpoints) so emissions are never duplicated. No-op
    until a stream has created the hub: with no subscriber connected there is
    nobody to notify, and the ``connected`` snapshot covers later connections.
    """
    hub = getattr(app.state, "realtime_hub", None)
    if hub is None:
        return
    hub.publish_notification(note.user_id, _wire(note))


async def _stream_snapshot(request: Request, user_id: str) -> list[dict[str, Any]]:
    """Latest notifications for the connecting SSE client, best effort.

    Only this initial snapshot needs MongoDB — live events do not — so a
    missing/unreachable store degrades to ``snapshot: []`` (logged) instead of
    refusing the connection: clients keep realtime and can fall back to the
    REST list for history.
    """
    repository: NotificationMongoRepository | None = getattr(
        request.app.state, "notification_repository", None
    )
    if repository is None:
        return []
    try:
        items, _total = await repository.list_for_user(
            user_id, limit=_STREAM_SNAPSHOT_LIMIT
        )
    except NotificationStoreError as exc:
        logger.warning("notifications stream snapshot degraded (continuing): %s", exc)
        return []
    return [_wire(note) for note in items]


@notifications_router.get("/notifications")
async def list_notifications(
    request: Request,
    read: bool | None = Query(default=None),
    category: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> APIResponse[list[dict[str, Any]]]:
    user_id = _current_user(request)
    notification_type = _category_type(category)
    repository = _repository(request)
    try:
        items, total = await repository.list_for_user(
            user_id,
            read=read,
            notification_type=notification_type,
            limit=limit,
            offset=offset,
        )
    except NotificationStoreError as exc:
        raise _store_error(exc, "list") from exc
    page = (offset // limit) + 1
    return APIResponse[list[dict[str, Any]]](
        data=[_wire(note) for note in items],
        meta=Meta(
            request_id=None,
            pagination=PaginationMeta(
                page=page,
                limit=limit,
                total=total,
                has_next=(offset + len(items)) < total,
                has_prev=offset > 0,
            ),
        ),
    )


def _stream_user(request: Request) -> str:
    """Caller identity for the SSE stream (issues #550/#551).

    The browser ``EventSource`` used by the frontend cannot send request
    headers, so the stream falls back to the short-lived access JWT in the
    ``?access_token=`` query parameter when no header identity resolves. The
    token is verified exactly like the header bearer (same ``verify_access``
    claims), and REST endpoints keep the header-only contract.
    """
    try:
        return _current_user(request)
    except HTTPException:
        pass
    token = request.query_params.get("access_token")
    if token:
        claims = verify_access(token)
        if claims and claims.get("sub"):
            return str(claims["sub"])
    raise HTTPException(status_code=401, detail="unauthorized")


@notifications_router.get(
    "/notifications/stream",
    summary="Live notification events (SSE)",
    description=(
        "Server-Sent Events for the JWT caller: ``connected`` (carrying a "
        "snapshot of the latest notifications) is emitted first, then "
        "``notification_created`` reacts to every insertion and ``ping`` "
        "keeps the connection warm every 15s (issue #550). Accepts the JWT "
        "via ``Authorization`` header or ``?access_token=`` for EventSource "
        "clients (issue #551)."
    ),
)
async def stream_notifications(request: Request) -> StreamingResponse:
    """Per-user SSE stream: identity from the JWT, same as the REST endpoints (#548)."""
    user_id = _stream_user(request)
    hub = _hub(request)
    # Subscribe before reading the snapshot so an insertion racing the query
    # is queued instead of lost (possible duplicate, never a gap); the frames
    # themselves still start with connected+snapshot before any live event.
    queue = hub.subscribe_notifications(user_id)
    try:
        snapshot = await _stream_snapshot(request, user_id)
    except BaseException:
        hub.unsubscribe_notifications(user_id, queue)
        raise

    async def generate() -> AsyncGenerator[str, None]:
        try:
            yield _sse("connected", {"userId": user_id, "snapshot": snapshot})
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
            hub.unsubscribe_notifications(user_id, queue)

    return StreamingResponse(generate(), media_type="text/event-stream", headers=_SSE_HEADERS)


@notifications_router.patch("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    request: Request,
) -> APIResponse[dict[str, Any]]:
    user_id = _current_user(request)
    repository = _repository(request)
    try:
        updated = await repository.mark_read(notification_id, user_id)
    except NotificationStoreError as exc:
        raise _store_error(exc, "mark read") from exc
    if updated is None:
        raise HTTPException(status_code=404, detail="notification not found")
    return APIResponse[dict[str, Any]](data=_wire(updated))


@notifications_router.post("/notifications/mark-all-read")
async def mark_all_notifications_read(request: Request) -> APIResponse[dict[str, Any]]:
    user_id = _current_user(request)
    repository = _repository(request)
    try:
        matched = await repository.mark_all_read(user_id)
    except NotificationStoreError as exc:
        raise _store_error(exc, "mark all read") from exc
    return APIResponse[dict[str, Any]](data={"matchedCount": matched})


@notifications_router.delete("/notifications/{notification_id}")
async def delete_notification(notification_id: str, request: Request) -> APIResponse[dict[str, Any]]:
    user_id = _current_user(request)
    repository = _repository(request)
    try:
        deleted = await repository.delete(notification_id, user_id)
    except NotificationStoreError as exc:
        raise _store_error(exc, "delete") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="notification not found")
    return APIResponse[dict[str, Any]](data={"id": notification_id, "deleted": True})


@notifications_router.post("/notifications/clear-all")
async def clear_notifications(
    request: Request,
    only_read: bool = Query(default=False, alias="onlyRead"),
) -> APIResponse[dict[str, Any]]:
    user_id = _current_user(request)
    repository = _repository(request)
    try:
        deleted = await repository.clear_all(user_id, only_read=only_read)
    except NotificationStoreError as exc:
        raise _store_error(exc, "clear all") from exc
    return APIResponse[dict[str, Any]](data={"deletedCount": deleted})
