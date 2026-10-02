"""Chat conversations/messages repository backed by MongoDB (motor) — issue #537.

Every participant, sender, reader and reactor reference is the unique
immutable user_id from the PostgreSQL Auth Store (#526/#527). Operations
degrade to a typed ChatStoreError (log + raise) when MongoDB is not
configured or unreachable, never breaking the rest of the API.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from socialseed_tasker.infrastructure.mongo.client import get_chat_database

logger = logging.getLogger(__name__)

CONVERSATION_TYPES = ("direct", "group")
MESSAGE_TYPES = ("text", "code", "system")


class ChatStoreError(Exception):
    """Chat MongoDB operation failed or persistence is not configured."""


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _object_id(value: str) -> Any:
    from bson import ObjectId

    try:
        return ObjectId(value)
    except Exception as exc:
        raise ChatStoreError(f"invalid document id: {value}") from exc


def _serialize(doc: Any) -> dict[str, Any]:
    """Normalize a Mongo document: expose string id and ISO-8601 datetimes."""
    out: dict[str, Any] = {}
    for key, value in (doc or {}).items():
        if key == "_id":
            out["id"] = str(value)
        elif isinstance(value, datetime):
            out[key] = value.isoformat()
        else:
            out[key] = value
    if "conversation_id" in out:
        out["conversation_id"] = str(out["conversation_id"])
    return out


class ChatMongoRepository:
    """Async chat persistence operations consumed by REST (#539) and Socket.IO (#538)."""

    def __init__(self, database: Any | None = None) -> None:
        self._database = database

    def _collection(self, name: str) -> Any:
        db = self._database if self._database is not None else get_chat_database()
        if db is None:
            raise ChatStoreError("MongoDB chat store not configured (TASKER_MONGO_URL unset)")
        try:
            return db[name]
        except Exception as exc:
            logger.warning("chat mongo collection %s unavailable: %s", name, exc)
            raise ChatStoreError(f"MongoDB chat store unavailable: {exc}") from exc

    async def list_conversations(self, user_id: str) -> list[dict[str, Any]]:
        """List conversations where user participates, most recently updated first."""
        if not user_id:
            raise ChatStoreError("user_id is required")
        try:
            coll = self._collection("conversations")
            cursor = coll.find({"participant_ids": user_id}).sort("updated_at", -1)
            docs: Any = await cursor.to_list(length=None)
            return [_serialize(d) for d in docs]
        except ChatStoreError:
            raise
        except Exception as exc:
            logger.warning("chat list_conversations failed for %s: %s", user_id, exc)
            raise ChatStoreError(f"list conversations failed: {exc}") from exc

    async def create_or_get_conversation(
        self,
        participant_ids: list[str],
        conversation_type: str = "direct",
        title: str | None = None,
    ) -> dict[str, Any]:
        """Create a conversation; for direct chats return the existing pair conversation."""
        participants = sorted({str(pid).strip() for pid in participant_ids if str(pid).strip()})
        if not participants:
            raise ChatStoreError("participant_ids is required")
        if conversation_type not in CONVERSATION_TYPES:
            raise ChatStoreError(f"invalid conversation type: {conversation_type}")
        try:
            coll = self._collection("conversations")
            if conversation_type == "direct" and len(participants) == 2:
                existing: Any = await coll.find_one(
                    {"participant_ids": {"$all": participants, "$size": len(participants)}}
                )
                if existing:
                    return _serialize(existing)
            now = _utcnow()
            doc: dict[str, Any] = {
                "title": title,
                "type": conversation_type,
                "participant_ids": participants,
                "pinned_by": [],
                "created_at": now,
                "updated_at": now,
            }
            result: Any = await coll.insert_one(doc)
            doc["_id"] = result.inserted_id
            return _serialize(doc)
        except ChatStoreError:
            raise
        except Exception as exc:
            logger.warning("chat create_or_get_conversation failed: %s", exc)
            raise ChatStoreError(f"create conversation failed: {exc}") from exc

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Fetch one conversation by id; None when it does not exist."""
        if not conversation_id:
            raise ChatStoreError("conversation_id is required")
        try:
            coll = self._collection("conversations")
            doc: Any = await coll.find_one({"_id": _object_id(conversation_id)})
            return _serialize(doc) if doc else None
        except ChatStoreError:
            raise
        except Exception as exc:
            logger.warning("chat get_conversation failed for %s: %s", conversation_id, exc)
            raise ChatStoreError(f"get conversation failed: {exc}") from exc

    async def list_messages(
        self,
        conversation_id: str,
        limit: int = 50,
        before: str | None = None,
    ) -> list[dict[str, Any]]:
        """Paginate messages (chronological); before is an ISO-8601 created_at cursor."""
        if not conversation_id:
            raise ChatStoreError("conversation_id is required")
        query: dict[str, Any] = {"conversation_id": str(conversation_id)}
        if before:
            try:
                query["created_at"] = {"$lt": datetime.fromisoformat(before)}
            except ValueError as exc:
                raise ChatStoreError(f"invalid before cursor: {before}") from exc
        try:
            coll = self._collection("messages")
            cursor = coll.find(query).sort("created_at", -1)
            docs: Any = await cursor.to_list(length=max(1, min(int(limit), 200)))
            page = list(docs)
            page.reverse()
            return [_serialize(d) for d in page]
        except ChatStoreError:
            raise
        except Exception as exc:
            logger.warning("chat list_messages failed for %s: %s", conversation_id, exc)
            raise ChatStoreError(f"list messages failed: {exc}") from exc

    async def toggle_pin(self, conversation_id: str, user_id: str) -> dict[str, Any]:
        """Add or remove user_id from the conversation pinned_by array."""
        if not conversation_id or not user_id:
            raise ChatStoreError("conversation_id and user_id are required")
        try:
            coll = self._collection("conversations")
            doc: Any = await coll.find_one({"_id": _object_id(conversation_id)})
            if doc is None:
                raise ChatStoreError(f"conversation not found: {conversation_id}")
            pinned = [str(u) for u in doc.get("pinned_by", [])]
            if user_id in pinned:
                await coll.update_one({"_id": doc["_id"]}, {"$pull": {"pinned_by": user_id}})
            else:
                await coll.update_one({"_id": doc["_id"]}, {"$addToSet": {"pinned_by": user_id}})
            updated: Any = await coll.find_one({"_id": doc["_id"]})
            return _serialize(updated or doc)
        except ChatStoreError:
            raise
        except Exception as exc:
            logger.warning("chat toggle_pin failed for %s: %s", conversation_id, exc)
            raise ChatStoreError(f"toggle pin failed: {exc}") from exc

    async def insert_message(
        self,
        conversation_id: str,
        sender_id: str,
        text: str,
        message_type: str = "text",
    ) -> dict[str, Any]:
        """Insert a message from sender_id and bump the conversation updated_at."""
        if not conversation_id or not sender_id:
            raise ChatStoreError("conversation_id and sender_id are required")
        if message_type not in MESSAGE_TYPES:
            raise ChatStoreError(f"invalid message type: {message_type}")
        if not text:
            raise ChatStoreError("text is required")
        try:
            now = _utcnow()
            doc: dict[str, Any] = {
                "conversation_id": str(conversation_id),
                "sender_id": str(sender_id),
                "text": text,
                "type": message_type,
                "read_by": [str(sender_id)],
                "reactions": [],
                "created_at": now,
            }
            msg_coll = self._collection("messages")
            result: Any = await msg_coll.insert_one(doc)
            doc["_id"] = result.inserted_id
            try:
                conv_coll = self._collection("conversations")
                await conv_coll.update_one(
                    {"_id": _object_id(conversation_id)}, {"$set": {"updated_at": now}}
                )
            except ChatStoreError:
                raise
            except Exception as bump_exc:
                logger.warning("chat conversation updated_at bump failed: %s", bump_exc)
            return _serialize(doc)
        except ChatStoreError:
            raise
        except Exception as exc:
            logger.warning("chat insert_message failed for %s: %s", conversation_id, exc)
            raise ChatStoreError(f"insert message failed: {exc}") from exc

    async def mark_as_read(self, conversation_id: str, user_id: str) -> dict[str, Any]:
        """Add user_id to read_by across the conversation messages (idempotent)."""
        if not conversation_id or not user_id:
            raise ChatStoreError("conversation_id and user_id are required")
        try:
            coll = self._collection("messages")
            result: Any = await coll.update_many(
                {"conversation_id": str(conversation_id)},
                {"$addToSet": {"read_by": str(user_id)}},
            )
            return {
                "conversation_id": str(conversation_id),
                "user_id": str(user_id),
                "matched_count": int(result.matched_count),
            }
        except ChatStoreError:
            raise
        except Exception as exc:
            logger.warning("chat mark_as_read failed for %s: %s", conversation_id, exc)
            raise ChatStoreError(f"mark as read failed: {exc}") from exc

    async def set_reaction(
        self,
        conversation_id: str,
        message_id: str,
        user_id: str,
        emoji: str,
    ) -> dict[str, Any]:
        """Toggle the caller's reaction: remove it if present, else set {user_id, emoji}."""
        if not conversation_id or not message_id or not user_id:
            raise ChatStoreError("conversation_id, message_id and user_id are required")
        if not emoji:
            raise ChatStoreError("emoji is required")
        try:
            coll = self._collection("messages")
            doc: Any = await coll.find_one(
                {"conversation_id": str(conversation_id), "_id": _object_id(message_id)}
            )
            if doc is None:
                raise ChatStoreError(f"message not found: {message_id}")
            existing = [r for r in (doc.get("reactions") or [])]
            had_reaction = any(str(r.get("user_id")) == str(user_id) for r in existing)
            reactions = [r for r in existing if str(r.get("user_id")) != str(user_id)]
            if not had_reaction:
                reactions.append({"user_id": str(user_id), "emoji": emoji})
            await coll.update_one({"_id": doc["_id"]}, {"$set": {"reactions": reactions}})
            updated: Any = await coll.find_one({"_id": doc["_id"]})
            return _serialize(updated or doc)
        except ChatStoreError:
            raise
        except Exception as exc:
            logger.warning("chat set_reaction failed for %s: %s", message_id, exc)
            raise ChatStoreError(f"set reaction failed: {exc}") from exc
