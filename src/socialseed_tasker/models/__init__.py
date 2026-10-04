"""Typed domain models for MongoDB persistence — issue #547."""

from socialseed_tasker.models.notification import (
    FRONTEND_CATEGORIES,
    Notification,
    NotificationSeverity,
    NotificationType,
)

__all__ = [
    "FRONTEND_CATEGORIES",
    "Notification",
    "NotificationSeverity",
    "NotificationType",
]
