"""Chat MongoDB persistence (motor) — issues #536/#537."""

from socialseed_tasker.infrastructure.mongo.chat_repository import (
    ChatMongoRepository,
    ChatStoreError,
)
from socialseed_tasker.infrastructure.mongo.client import (
    close_mongo,
    ensure_chat_indexes,
    get_chat_database,
    get_mongo_client,
)

__all__ = [
    "ChatMongoRepository",
    "ChatStoreError",
    "close_mongo",
    "ensure_chat_indexes",
    "get_chat_database",
    "get_mongo_client",
]
