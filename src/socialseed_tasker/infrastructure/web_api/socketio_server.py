"""Socket.IO realtime transport for chat — issue #538.

A ``python-socketio`` ``AsyncServer`` (async_mode="asgi") mounted over the
FastAPI app with ``socketio.ASGIApp`` so REST and Socket.IO share the same
port and process. The handshake validates the same JWTs as the REST layer
(#519/#527), one room per ``conversation_id``, and the named events below
are the transport notified by REST (#539) and consumed by the frontend
(#540). Room access is checked against the Mongo participant list (#537).

Events (server): ``join_room``, ``leave_room``, ``send_message``,
``typing_start``, ``typing_stop``, ``mark_as_read``.
Emitted to the room: ``new_message``, ``messages_read``, ``typing_start``,
``typing_stop``.

This module also owns the shared wire projections ``conversation_wire`` /
``message_wire``: every payload crossing the wire (Socket.IO acks, room
emissions and the REST chat endpoints of #539) is camelCase and matches the
frontend contract of #540 (``conversationId``, ``senderId``, ``content``,
``readBy``, ``createdAt``). Inbound events stay tolerant: room payloads
accept ``conversation_id`` or ``conversationId``.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Awaitable, Callable
from typing import Any
from urllib.parse import parse_qs

import socketio

from socialseed_tasker.auth.tokens import verify_access
from socialseed_tasker.infrastructure.mongo.chat_repository import (
    MESSAGE_TYPES,
    ChatMongoRepository,
    ChatStoreError,
)

logger = logging.getLogger(__name__)


def _allowed_origins() -> list[str]:
    """Board/nginx origin plus API origins; restricted list (never tokens in logs)."""
    origins: set[str] = set()
    for env in ("TASKER_FRONTEND_URL", "TASKER_API_ALLOW_ORIGINS"):
        raw = os.getenv(env, "")
        origins.update(part.strip() for part in raw.split(",") if part.strip())
    return sorted(origins) if origins else ["*"]


def _extract_token(environ: dict[str, Any], auth: dict[str, Any] | None) -> str | None:
    if isinstance(auth, dict):
        for key in ("token", "access_token"):
            value = auth.get(key)
            if isinstance(value, str) and value:
                return value[7:] if value.lower().startswith("bearer ") else value
    header = str(environ.get("HTTP_AUTHORIZATION") or "")
    if header.lower().startswith("bearer "):
        return header[7:]
    query = parse_qs(str(environ.get("QUERY_STRING") or ""))
    for key in ("token", "access_token"):
        values = query.get(key)
        if values and values[0]:
            return values[0]
    return None


def is_object_id(value: str) -> bool:
    return len(value) == 24 and all(c in "0123456789abcdef" for c in value.lower())


def _room(data: dict[str, Any] | None) -> str:
    payload = data or {}
    return str(payload.get("conversation_id") or payload.get("conversationId") or "")


def conversation_wire(doc: dict[str, Any]) -> dict[str, Any]:
    """Conversation document -> camelCase payload shared by REST and Socket.IO."""
    return {
        "id": str(doc.get("id", "")),
        "title": doc.get("title"),
        "type": str(doc.get("type", "direct")),
        "participantIds": [str(p) for p in doc.get("participant_ids", [])],
        "pinnedBy": [str(p) for p in doc.get("pinned_by", [])],
        "createdAt": doc.get("created_at"),
        "updatedAt": doc.get("updated_at"),
    }


def message_wire(doc: dict[str, Any]) -> dict[str, Any]:
    """Message document -> camelCase payload matching the frontend ChatMessage type."""
    reactions: dict[str, list[str]] = {}
    for reaction in doc.get("reactions") or []:
        emoji = str(reaction.get("emoji", ""))
        if emoji:
            reactions.setdefault(emoji, []).append(str(reaction.get("user_id", "")))
    wire: dict[str, Any] = {
        "id": str(doc.get("id", "")),
        "conversationId": str(doc.get("conversation_id", "")),
        "senderId": str(doc.get("sender_id", "")),
        "content": str(doc.get("text", "")),
        "type": str(doc.get("type", "text")),
        "readBy": [str(u) for u in doc.get("read_by", [])],
        "reactions": reactions,
        "createdAt": doc.get("created_at"),
    }
    if doc.get("updated_at") is not None:
        wire["updatedAt"] = doc["updated_at"]
    return wire


def _ok(payload: Any) -> dict[str, Any]:
    return {"data": payload, "error": None}


def _err(code: str, message: str) -> dict[str, Any]:
    return {"data": None, "error": {"code": code, "message": message}}


class _AccessDeniedError(Exception):
    """Room access denied with a machine-readable error code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ChatSocketIOServer:
    """AsyncServer wrapper: JWT handshake, one room per conversation, chat events."""

    def __init__(
        self,
        repository: ChatMongoRepository,
        session_store_provider: Callable[[], Any] | None = None,
    ) -> None:
        self.sio = socketio.AsyncServer(
            async_mode="asgi",
            cors_allowed_origins=_allowed_origins(),
        )
        self._repository = repository
        self._session_store_provider = session_store_provider
        self._users: dict[str, str] = {}
        self._register_handlers()

    def _authenticate(self, environ: dict[str, Any], auth: dict[str, Any] | None) -> str | None:
        token = _extract_token(environ, auth)
        if not token:
            return None
        claims = verify_access(token)
        if claims is None:
            return None
        session_id = claims.get("sid")
        if session_id and self._session_store_provider is not None:
            store = self._session_store_provider()
            if store is None or store.get(str(claims.get("sub", "")), str(session_id)) is None:
                return None
        user_id = claims.get("sub")
        return str(user_id) if user_id else None

    async def _participant(self, sid: str, conversation_id: str) -> str:
        user_id = self._users.get(sid)
        if user_id is None:
            raise _AccessDeniedError("UNAUTHENTICATED", "socket session not authenticated")
        cid = str(conversation_id or "")
        if not is_object_id(cid):
            raise _AccessDeniedError("VALIDATION_ERROR", "invalid conversation_id")
        conv = await self._repository.get_conversation(cid)
        if conv is None:
            raise _AccessDeniedError("NOT_FOUND", "conversation not found")
        if user_id not in [str(p) for p in conv.get("participant_ids", [])]:
            raise _AccessDeniedError("FORBIDDEN", "user is not a participant of this conversation")
        return user_id

    async def _guarded(
        self,
        sid: str,
        conversation_id: str,
        action: Callable[[str], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:
        try:
            user_id = await self._participant(sid, conversation_id)
            return _ok(await action(user_id))
        except _AccessDeniedError as denied:
            return _err(denied.code, denied.message)
        except ChatStoreError as exc:
            logger.warning("chat socket degraded: %s", exc)
            return _err("CHAT_UNAVAILABLE", str(exc))

    def _register_handlers(self) -> None:
        sio = self.sio

        async def connect(sid: str, environ: dict[str, Any], auth: dict[str, Any] | None = None) -> None:
            user_id = self._authenticate(environ, auth)
            if user_id is None:
                logger.warning("socket.io connect rejected (sid=%s): invalid or expired token", sid)
                raise socketio.exceptions.ConnectionRefusedError("authentication failed")
            self._users[sid] = user_id
            logger.info("socket.io connected (sid=%s, user=%s)", sid, user_id)

        async def disconnect(sid: str) -> None:
            self._users.pop(sid, None)
            logger.info("socket.io disconnected (sid=%s)", sid)

        async def join_room(sid: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
            cid = _room(data)

            async def action(user_id: str) -> dict[str, Any]:
                await sio.enter_room(sid, room=cid)
                logger.info("socket.io join_room user=%s conversation=%s", user_id, cid)
                return {"conversationId": cid, "joined": True}

            return await self._guarded(sid, cid, action)

        async def leave_room(sid: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
            cid = _room(data)

            async def action(user_id: str) -> dict[str, Any]:
                await sio.leave_room(sid, room=cid)
                logger.info("socket.io leave_room user=%s conversation=%s", user_id, cid)
                return {"conversationId": cid, "left": True}

            return await self._guarded(sid, cid, action)

        async def send_message(sid: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
            payload = data or {}
            cid = _room(payload)
            text = str(payload.get("text") or payload.get("content") or "")
            message_type = str(payload.get("type") or "text")

            async def action(user_id: str) -> dict[str, Any]:
                if not text:
                    raise _AccessDeniedError("VALIDATION_ERROR", "text is required")
                if message_type not in MESSAGE_TYPES:
                    raise _AccessDeniedError("VALIDATION_ERROR", f"invalid message type: {message_type}")
                message = await self._repository.insert_message(cid, user_id, text, message_type)
                wire = message_wire(message)
                await sio.emit("new_message", wire, room=cid)
                return wire

            return await self._guarded(sid, cid, action)

        async def _typing(sid: str, data: dict[str, Any] | None, event: str) -> dict[str, Any]:
            cid = _room(data)

            async def action(user_id: str) -> dict[str, Any]:
                await sio.emit(
                    event,
                    {"conversationId": cid, "userId": user_id},
                    room=cid,
                    skip_sid=sid,
                )
                return {"conversationId": cid, "typing": event == "typing_start"}

            return await self._guarded(sid, cid, action)

        async def typing_start(sid: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
            return await _typing(sid, data, "typing_start")

        async def typing_stop(sid: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
            return await _typing(sid, data, "typing_stop")

        sio.on("typing_start", typing_start)
        sio.on("typing_stop", typing_stop)

        async def mark_as_read(sid: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
            cid = _room(data)

            async def action(user_id: str) -> dict[str, Any]:
                result = await self._repository.mark_as_read(cid, user_id)
                wire = {
                    "conversationId": str(result.get("conversation_id", cid)),
                    "userId": str(result.get("user_id", user_id)),
                    "matchedCount": int(result.get("matched_count", 0)),
                }
                await sio.emit("messages_read", wire, room=cid)
                return wire

            return await self._guarded(sid, cid, action)

        sio.on("connect", connect)
        sio.on("disconnect", disconnect)
        sio.on("join_room", join_room)
        sio.on("leave_room", leave_room)
        sio.on("send_message", send_message)
        sio.on("mark_as_read", mark_as_read)

    def asgi(self, app: Any) -> Any:
        """Wrap the FastAPI app so uvicorn serves REST and /socket.io/ together."""
        return socketio.ASGIApp(self.sio, other_asgi_app=app)
