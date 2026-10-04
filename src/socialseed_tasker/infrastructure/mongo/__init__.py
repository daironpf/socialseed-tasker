"""Chat + notifications MongoDB persistence (motor) — issues #536/#537/#547."""

from socialseed_tasker.infrastructure.mongo.chat_repository import (
    ChatMongoRepository,
    ChatStoreError,
)
from socialseed_tasker.infrastructure.mongo.client import (
    close_mongo,
    ensure_chat_indexes,
    ensure_notification_indexes,
    get_chat_database,
    get_mongo_client,
)
from socialseed_tasker.infrastructure.mongo.notification_repository import (
    NotificationMongoRepository,
    NotificationStoreError,
)

__all__ = [
    "ChatMongoRepository",
    "ChatStoreError",
    "NotificationMongoRepository",
    "NotificationStoreError",
    "close_mongo",
    "ensure_chat_indexes",
    "ensure_notification_indexes",
    "get_chat_database",
    "get_mongo_client",
]
