"""Lazy async MongoDB (motor) client for chat and notifications persistence — issues #537/#547.

Safe fallback from #536: without TASKER_MONGO_URL no client is created and
every entrypoint returns None so the rest of the API keeps working. The
client is cached per process and closed from the app lifespan.
"""

from __future__ import annotations

import logging
import os
from typing import Any
from urllib.parse import urlparse

from socialseed_tasker.config.storage import get_mongo_url

logger = logging.getLogger(__name__)

DEFAULT_CHAT_DB = "tasker_chat"

_client: Any | None = None
_attempted = False


def _database_from_url(url: str) -> str:
    try:
        return urlparse(url).path.lstrip("/").split("?")[0]
    except Exception:
        return ""


def get_mongo_client() -> Any | None:
    """Return the cached AsyncIOMotorClient, or None when Mongo is not configured."""
    global _client, _attempted
    if _attempted:
        return _client
    _attempted = True
    url = get_mongo_url()
    if not url:
        logger.info("mongo not configured (TASKER_MONGO_URL unset): chat persistence disabled")
        return None
    try:
        from motor.motor_asyncio import AsyncIOMotorClient

        _client = AsyncIOMotorClient(url, serverSelectionTimeoutMS=2000)
        logger.info("mongo chat client created for %s", urlparse(url).netloc)
    except Exception as exc:
        logger.warning("mongo client init failed (chat disabled): %s", exc)
        _client = None
    return _client


def get_chat_database() -> Any | None:
    """Return the chat database (TASKER_MONGO_DB override, URL path, else tasker_chat) or None."""
    client = get_mongo_client()
    if client is None:
        return None
    db_name = os.getenv("TASKER_MONGO_DB") or _database_from_url(get_mongo_url() or "") or DEFAULT_CHAT_DB
    return client[db_name]


async def ensure_chat_indexes() -> bool:
    """Create chat indexes idempotently (create_index is repeatable). False when Mongo is unavailable."""
    db = get_chat_database()
    if db is None:
        return False
    try:
        await db.conversations.create_index([("participant_ids", 1)])
        await db.messages.create_index([("conversation_id", 1)])
        await db.messages.create_index([("conversation_id", 1), ("created_at", -1)])
        await db.messages.create_index([("created_at", -1)])
        logger.info(
            "chat mongo indexes ensured (conversations.participant_ids, messages.conversation_id/created_at)"
        )
        return True
    except Exception as exc:
        logger.warning("chat mongo index bootstrap failed (continuing): %s", exc)
        return False


async def ensure_notification_indexes() -> bool:
    """Create notifications indexes idempotently (create_index is repeatable). False when Mongo is unavailable."""
    db = get_chat_database()
    if db is None:
        return False
    try:
        from socialseed_tasker.models.notification import NOTIFICATIONS_COLLECTION

        await db[NOTIFICATIONS_COLLECTION].create_index([("user_id", 1), ("read", 1)])
        await db[NOTIFICATIONS_COLLECTION].create_index([("created_at", -1)])
        logger.info("notification mongo indexes ensured (notifications.user_id/read, created_at)")
        return True
    except Exception as exc:
        logger.warning("notification mongo index bootstrap failed (continuing): %s", exc)
        return False


def close_mongo() -> None:
    """Close the cached client and reset the cache (app shutdown / tests)."""
    global _client, _attempted
    client = _client
    _client = None
    _attempted = False
    if client is not None:
        try:
            client.close()
        except Exception as exc:
            logger.warning("mongo client close failed: %s", exc)
