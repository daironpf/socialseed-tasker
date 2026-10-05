"""Notifications repository backed by MongoDB (motor) — issue #547.

Shares the chat Mongo client/database (TASKER_MONGO_URL, no new env var).
Operations degrade to a typed NotificationStoreError (log + raise) when
MongoDB is not configured or unreachable, never breaking the rest of the
API. Consumed by the REST endpoint (#548) and the install flow (#549).
"""

from __future__ import annotations

import logging
from typing import Any

from socialseed_tasker.infrastructure.mongo.client import get_chat_database
from socialseed_tasker.models.notification import NOTIFICATIONS_COLLECTION, Notification

logger = logging.getLogger(__name__)


class NotificationStoreError(Exception):
    """Notifications MongoDB operation failed or persistence is not configured."""


def _object_id(value: str) -> Any:
    from bson import ObjectId

    try:
        return ObjectId(value)
    except Exception as exc:
        raise NotificationStoreError(f"invalid document id: {value}") from exc


class NotificationMongoRepository:
    """Async notification persistence consumed by REST (#548) and setup (#549)."""

    def __init__(self, database: Any | None = None) -> None:
        self._database = database

    def _collection(self) -> Any:
        db = self._database if self._database is not None else get_chat_database()
        if db is None:
            raise NotificationStoreError("MongoDB notifications store not configured (TASKER_MONGO_URL unset)")
        try:
            return db[NOTIFICATIONS_COLLECTION]
        except Exception as exc:
            logger.warning("notifications mongo collection unavailable: %s", exc)
            raise NotificationStoreError(f"MongoDB notifications store unavailable: {exc}") from exc

    async def insert(self, notification: Notification) -> Notification:
        """Persist a notification and return it with the generated id."""
        try:
            doc = notification.to_document()
            coll = self._collection()
            result: Any = await coll.insert_one(doc)
            doc["_id"] = result.inserted_id
            stored = Notification.from_document(doc)
        except NotificationStoreError:
            raise
        except Exception as exc:
            logger.warning("notifications insert failed for %s: %s", notification.type, exc)
            raise NotificationStoreError(f"insert notification failed: {exc}") from exc
        if stored is None:
            raise NotificationStoreError("insert notification failed: stored document could not be read back")
        return stored

    async def get(self, notification_id: str) -> Notification | None:
        """Fetch one notification by id; None when it does not exist."""
        if not notification_id:
            raise NotificationStoreError("notification_id is required")
        try:
            coll = self._collection()
            doc: Any = await coll.find_one({"_id": _object_id(notification_id)})
            return Notification.from_document(doc) if doc else None
        except NotificationStoreError:
            raise
        except Exception as exc:
            logger.warning("notifications get failed for %s: %s", notification_id, exc)
            raise NotificationStoreError(f"get notification failed: {exc}") from exc

    async def list_for_user(
        self,
        user_id: str,
        *,
        read: bool | None = None,
        notification_type: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Notification], int]:
        """Page through a user's notifications (created_at desc) plus the total count."""
        if not user_id:
            raise NotificationStoreError("user_id is required")
        query: dict[str, Any] = {"user_id": user_id}
        if read is not None:
            query["read"] = read
        if notification_type:
            query["type"] = notification_type
        try:
            coll = self._collection()
            total = int(await coll.count_documents(query))
            cursor: Any = coll.find(query).sort("created_at", -1)
            docs: Any = await cursor.skip(max(int(offset), 0)).limit(max(int(limit), 1)).to_list(
                length=max(int(limit), 1)
            )
            items = [n for n in (Notification.from_document(d) for d in docs) if n is not None]
            return items, total
        except NotificationStoreError:
            raise
        except Exception as exc:
            logger.warning("notifications list failed for %s: %s", user_id, exc)
            raise NotificationStoreError(f"list notifications failed: {exc}") from exc

    async def mark_read(self, notification_id: str, user_id: str) -> Notification | None:
        """Set read=True on a notification owned by user_id; None when missing/foreign."""
        if not notification_id or not user_id:
            raise NotificationStoreError("notification_id and user_id are required")
        try:
            coll = self._collection()
            query: dict[str, Any] = {"_id": _object_id(notification_id), "user_id": user_id}
            result: Any = await coll.update_one(query, {"$set": {"read": True}})
            if int(getattr(result, "matched_count", 0) or 0) == 0:
                return None
            doc: Any = await coll.find_one(query)
            return Notification.from_document(doc) if doc else None
        except NotificationStoreError:
            raise
        except Exception as exc:
            logger.warning("notifications mark_read failed for %s: %s", notification_id, exc)
            raise NotificationStoreError(f"mark notification read failed: {exc}") from exc

    async def mark_all_read(self, user_id: str) -> int:
        """Mark every unread notification of user_id as read; returns the matched count."""
        if not user_id:
            raise NotificationStoreError("user_id is required")
        try:
            coll = self._collection()
            result: Any = await coll.update_many(
                {"user_id": user_id, "read": False}, {"$set": {"read": True}}
            )
            return int(getattr(result, "matched_count", 0) or 0)
        except NotificationStoreError:
            raise
        except Exception as exc:
            logger.warning("notifications mark_all_read failed for %s: %s", user_id, exc)
            raise NotificationStoreError(f"mark all read failed: {exc}") from exc

    async def delete(self, notification_id: str, user_id: str) -> bool:
        """Delete one notification owned by user_id; False when missing/foreign."""
        if not notification_id or not user_id:
            raise NotificationStoreError("notification_id and user_id are required")
        try:
            coll = self._collection()
            result: Any = await coll.delete_one(
                {"_id": _object_id(notification_id), "user_id": user_id}
            )
            return int(getattr(result, "deleted_count", 0) or 0) > 0
        except NotificationStoreError:
            raise
        except Exception as exc:
            logger.warning("notifications delete failed for %s: %s", notification_id, exc)
            raise NotificationStoreError(f"delete notification failed: {exc}") from exc

    async def clear_all(self, user_id: str, only_read: bool = False) -> int:
        """Delete all of the user's notifications (optionally only read ones); returns the count."""
        if not user_id:
            raise NotificationStoreError("user_id is required")
        query: dict[str, Any] = {"user_id": user_id}
        if only_read:
            query["read"] = True
        try:
            coll = self._collection()
            result: Any = await coll.delete_many(query)
            return int(getattr(result, "deleted_count", 0) or 0)
        except NotificationStoreError:
            raise
        except Exception as exc:
            logger.warning("notifications clear_all failed for %s: %s", user_id, exc)
            raise NotificationStoreError(f"clear notifications failed: {exc}") from exc
