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
