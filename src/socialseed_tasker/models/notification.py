"""Notification schema for MongoDB persistence — issue #547.

The `notifications` collection is consumed by the REST API (#548), seeded
by the install flow (#549) and rendered by the frontend NotificationCenter
(#551). `id` holds the string form of the Mongo ObjectId and is exposed as
`id` (never `_id`) in JSON, as required by notas.md.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class NotificationType(str, Enum):
    """Notification kinds stored in MongoDB (notas.md Issue #1)."""

    MENTION = "MENTION"
    HITL = "HITL"
    CONSTRAINT_VIOLATION = "CONSTRAINT_VIOLATION"
    AGENT_FAILURE = "AGENT_FAILURE"
    SLA = "SLA"
    WELCOME = "WELCOME"


#: Mongo collection that holds the notification documents (shared by
#: ``ensure_notification_indexes`` (client.py) and the repository).
NOTIFICATIONS_COLLECTION = "notifications"


class NotificationSeverity(str, Enum):
    """Emergency / Warning / Info buckets used by the NotificationCenter."""

    EMERGENCY = "EMERGENCY"
    WARNING = "WARNING"
    INFO = "INFO"


# Backend type -> frontend NotificationCategory (frontend/src/types/notifications.ts).
# The first five already exist in the UI; welcome is the new category added by #549/#551.
FRONTEND_CATEGORIES: dict[NotificationType, str] = {
    NotificationType.MENTION: "mention",
    NotificationType.HITL: "hitl",
    NotificationType.CONSTRAINT_VIOLATION: "constraint_violation",
    NotificationType.AGENT_FAILURE: "agent_failure",
    NotificationType.SLA: "sla",
    NotificationType.WELCOME: "welcome",
}


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class Notification(BaseModel):
    """A single notification document (collection `notifications`)."""

    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    id: str | None = Field(default=None, alias="_id")
    user_id: str = Field(min_length=1)
    type: NotificationType
    severity: NotificationSeverity
    title: str = Field(min_length=1)
    message: str = Field(min_length=1)
    read: bool = False
    requires_action: bool = False
    link_to: str | None = None
    hitl_request_id: str | None = None
    channel: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, value: Any) -> str | None:
        """Accept a bson ObjectId (or any stringable value) and expose it as `id`."""
        if value is None or value == "":
            return None
        return str(value)

    @field_validator("created_at")
    @classmethod
    def _ensure_utc(cls, value: datetime) -> datetime:
        return _as_utc(value)

    @property
    def category(self) -> str:
        """Frontend `NotificationCategory` for this notification's type."""
        return FRONTEND_CATEGORIES[self.type]

    def to_document(self) -> dict[str, Any]:
        """Mongo-ready document: no `id` (Mongo generates `_id`), enums as plain values."""
        data = self.model_dump(mode="python", exclude={"id"})
        data["type"] = self.type.value
        data["severity"] = self.severity.value
        data["created_at"] = self.created_at
        return data

    @classmethod
    def from_document(cls, doc: Any) -> Notification | None:
        """Build a Notification from a stored document (`_id` -> `id`, ISO datetimes)."""
        if not doc:
            return None
        data: dict[str, Any] = dict(doc)
        if "_id" in data:
            data["id"] = data.pop("_id")
        return cls.model_validate(data)
