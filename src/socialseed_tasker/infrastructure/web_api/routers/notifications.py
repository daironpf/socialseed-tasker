"""REST notification endpoints: list, read state and cleanup — issue #548.

Endpoints under ``/api/v1/notifications/*`` return the shared ``APIResponse``
envelope (camelCase: ``createdAt``, ``requiresAction``, ``hitlRequestId``,
``linkTo``). The caller identity always comes from the request JWT (never
from the body) so one user can never read, mark or delete another user's
notifications — foreign/unknown ids answer 404 without leaking existence.
Persistence goes through the Mongo repository (#547) and degrades to a typed
503 when MongoDB is not configured or unreachable.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from socialseed_tasker.infrastructure.mongo.notification_repository import (
    NotificationMongoRepository,
    NotificationStoreError,
)
from socialseed_tasker.infrastructure.web_api.routers.chat import _current_user
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
