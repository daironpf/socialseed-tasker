"""REST chat endpoints: conversations, history and pinning — issue #539.

Endpoints under ``/api/v1/chat/*`` return the shared ``APIResponse`` envelope
(camelCase) and resolve the caller from the same identity sources as the rest
of the API (#519/#527): JWT claims first, then API-key tokens, then the
OAuth session cookie (and ``X-User-ID`` while auth is disabled for local
development). Messages created over HTTP are persisted through the Mongo
repository (#537) and then broadcast with the injectable dispatcher wired in
``app.py`` to the Socket.IO server (#538) so room members receive them even
when the author is not connected over the socket.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from socialseed_tasker.auth.auth import load_auth_provider
from socialseed_tasker.auth.tokens import verify_access
from socialseed_tasker.infrastructure.mongo.chat_repository import (
    CONVERSATION_TYPES,
    MESSAGE_TYPES,
    ChatMongoRepository,
    ChatStoreError,
)
from socialseed_tasker.infrastructure.web_api.schemas import APIResponse
from socialseed_tasker.infrastructure.web_api.socketio_server import (
    conversation_wire,
    is_object_id,
    message_wire,
)

chat_router = APIRouter()
logger = logging.getLogger(__name__)


class CamelModel(BaseModel):
    """Request model serialised to camelCase (frontend contract)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class ConversationCreateRequest(CamelModel):
    participant_ids: list[str] = Field(default_factory=list)
    type: str = "direct"
    title: str | None = None


class MessageCreateRequest(CamelModel):
    text: str = ""
    type: str = "text"


def _bearer_token(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
        return token or None
    return None


def _resolve_user(request: Request) -> str | None:
    """Caller identity: JWT sub, API-key user, OAuth session, or dev header."""
    token = _bearer_token(request)
    if token:
        claims = verify_access(token)
        if claims and claims.get("sub"):
            return str(claims["sub"])
        user_id = load_auth_provider().verify_token(token)
        if user_id:
            return str(user_id)
    from socialseed_tasker.auth.oauth import SESSION_COOKIE_NAME

    sid = request.cookies.get(SESSION_COOKIE_NAME)
    if sid:
        session_store = getattr(request.app.state, "session_store", None)
        if session_store:
            session = session_store.get(sid)
            if session:
                claims = session.get("claims", {})
                ident = claims.get("preferred_username") or claims.get("sub")
                if ident:
                    return str(ident)
    if os.getenv("TASKER_AUTH_ENABLED", "false").lower() != "true":
        header_user = request.headers.get("x-user-id")
        if header_user:
            return header_user
    return None


def _current_user(request: Request) -> str:
    user_id = _resolve_user(request)
    if user_id is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return user_id


def _repository(request: Request) -> ChatMongoRepository:
    repository: ChatMongoRepository | None = getattr(request.app.state, "chat_repository", None)
    if repository is None:
        raise HTTPException(status_code=503, detail="chat store unavailable")
    return repository


def _store_error(exc: ChatStoreError, action: str) -> HTTPException:
    logger.warning("chat %s degraded: %s", action, exc)
    return HTTPException(status_code=503, detail="chat store unavailable")


async def _emit(request: Request, event: str, data: dict[str, Any], room: str) -> None:
    emit = getattr(request.app.state, "chat_emit", None)
    if emit is None:
        logger.warning("chat emitter not wired; dropping %s event", event)
        return
    await emit(event, data, room)


async def _owned_conversation(request: Request, user_id: str, conversation_id: str) -> dict[str, Any]:
    if not is_object_id(conversation_id):
        raise ValueError("invalid conversation_id")
    repository = _repository(request)
    try:
        conversation = await repository.get_conversation(conversation_id)
    except ChatStoreError as exc:
        raise _store_error(exc, "get conversation") from exc
    if conversation is None:
        raise HTTPException(status_code=404, detail="conversation not found")
    if user_id not in [str(p) for p in conversation.get("participant_ids", [])]:
        raise HTTPException(status_code=403, detail="forbidden")
    return conversation


@chat_router.get("/chat/conversations")
async def list_conversations(request: Request) -> APIResponse[list[dict[str, Any]]]:
    user_id = _current_user(request)
    repository = _repository(request)
    try:
        conversations = await repository.list_conversations(user_id)
        items: list[dict[str, Any]] = []
        for conversation in conversations:
            wire = conversation_wire(conversation)
            last = await repository.latest_message(str(conversation.get("id", "")))
            if last is not None:
                wire["lastMessage"] = message_wire(last)
            items.append(wire)
    except ChatStoreError as exc:
        raise _store_error(exc, "list conversations") from exc
    return APIResponse[list[dict[str, Any]]](data=items)


@chat_router.post("/chat/conversations")
async def create_conversation(
    body: ConversationCreateRequest,
    request: Request,
) -> APIResponse[dict[str, Any]]:
    user_id = _current_user(request)
    conversation_type = body.type
    if conversation_type not in CONVERSATION_TYPES:
        raise ValueError(f"invalid conversation type: {conversation_type}")
    raw = [str(pid).strip() for pid in body.participant_ids]
    if any(not pid for pid in raw):
        raise ValueError("participant_ids contains empty values")
    if len(set(raw)) != len(raw):
        raise ValueError("participant_ids contains duplicates")
    participants = sorted({*raw, user_id})
    if conversation_type == "direct" and len(participants) != 2:
        raise ValueError("direct conversation requires exactly two participants")
    if len(participants) < 2:
        raise ValueError("conversation requires at least two participants")
    repository = _repository(request)
    try:
        conversation = await repository.create_or_get_conversation(
            participants, conversation_type, body.title
        )
    except ChatStoreError as exc:
        raise _store_error(exc, "create conversation") from exc
    return APIResponse[dict[str, Any]](data=conversation_wire(conversation))


@chat_router.get("/chat/conversations/{conversation_id}/messages")
async def list_messages(
    conversation_id: str,
    request: Request,
    limit: int = Query(default=50, ge=1, le=200),
    before: str | None = Query(default=None),
) -> APIResponse[dict[str, Any]]:
    user_id = _current_user(request)
    await _owned_conversation(request, user_id, conversation_id)
    if before is not None:
        try:
            datetime.fromisoformat(before)
        except ValueError as exc:
            raise ValueError(f"invalid before cursor: {before}") from exc
    repository = _repository(request)
    try:
        messages = await repository.list_messages(conversation_id, limit=limit, before=before)
    except ChatStoreError as exc:
        raise _store_error(exc, "list messages") from exc
    items = [message_wire(message) for message in messages]
    next_cursor = items[0]["createdAt"] if len(items) == limit and items else None
    return APIResponse[dict[str, Any]](
        data={"messages": items, "limit": limit, "nextCursor": next_cursor}
    )


@chat_router.post("/chat/conversations/{conversation_id}/pin")
async def toggle_pin(conversation_id: str, request: Request) -> APIResponse[dict[str, Any]]:
    user_id = _current_user(request)
    await _owned_conversation(request, user_id, conversation_id)
    repository = _repository(request)
    try:
        conversation = await repository.toggle_pin(conversation_id, user_id)
    except ChatStoreError as exc:
        raise _store_error(exc, "toggle pin") from exc
    return APIResponse[dict[str, Any]](data=conversation_wire(conversation))


@chat_router.post("/chat/conversations/{conversation_id}/messages")
async def create_message(
    conversation_id: str,
    body: MessageCreateRequest,
    request: Request,
) -> APIResponse[dict[str, Any]]:
    user_id = _current_user(request)
    await _owned_conversation(request, user_id, conversation_id)
    text = body.text.strip()
    if not text:
        raise ValueError("text is required")
    if body.type not in MESSAGE_TYPES:
        raise ValueError(f"invalid message type: {body.type}")
    repository = _repository(request)
    try:
        message = await repository.insert_message(conversation_id, user_id, text, body.type)
    except ChatStoreError as exc:
        raise _store_error(exc, "create message") from exc
    wire = message_wire(message)
    try:
        await _emit(request, "new_message", wire, str(conversation_id))
    except Exception as exc:
        logger.warning("chat new_message emission failed: %s", exc)
    return APIResponse[dict[str, Any]](data=wire)
