"""Sync queue and offline-first synchronization engine.

Provides queue-based sync for offline operations with retry logic
and conflict resolution.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

logger = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SyncOperation(str, Enum):
    """Types of sync operations."""

    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class SyncEntityType(str, Enum):
    """Types of entities that can be synced."""

    ISSUE = "issue"
    COMMENT = "comment"
    LABEL = "label"
    MILESTONE = "milestone"


class SyncStatus(str, Enum):
    """Status of sync queue items."""

    PENDING = "pending"
    PROCESSING = "processing"
    FAILED = "failed"
    COMPLETED = "completed"


@dataclass
class SyncQueueItem:
    """A single item in the sync queue."""

    id: UUID = field(default_factory=uuid4)
    operation: SyncOperation = SyncOperation.CREATE
    entity_type: SyncEntityType = SyncEntityType.ISSUE
    entity_id: UUID = field(default_factory=uuid4)
    payload: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    retry_count: int = 0
    status: SyncStatus = SyncStatus.PENDING
    last_error: str | None = None


class OfflineFirstSyncEngine:
    """Engine for offline-first synchronization.

    Queues operations when offline and processes them when connectivity
    is restored.
    """

    def __init__(
        self,
        batch_size: int = 50,
        retry_delay: float = 1.0,
    ) -> None:
        self._queue: list[SyncQueueItem] = []
        self._batch_size = batch_size
        self._retry_delay = retry_delay
        self._is_online = True
        self._github_adapter = None

    def set_github_adapter(self, adapter) -> None:
        """Set the GitHub adapter for syncing."""
        self._github_adapter = adapter

    def is_online(self) -> bool:
        """Check if currently online."""
        return self._is_online

    def set_online_status(self, online: bool) -> None:
        """Set the online status."""
        self._is_online = online

    def check_connectivity(self) -> bool:
        """Check network connectivity."""
        try:
            import httpx
        except ImportError:
            logger.warning("httpx not available, sync limited")
            self._is_online = False
            return False

        try:
            response = httpx.get("https://api.github.com", timeout=5.0)
            self._is_online = response.status_code < 500
            return self._is_online
        except Exception as e:
            logger.error(f"Sync connectivity check failed: {e}")
            self._is_online = False
            return False

    def enqueue(
        self,
        operation: str,
        entity_type: str,
        entity_id: str,
        payload: dict,
    ) -> SyncQueueItem:
        """Add an operation to the sync queue."""
        item = SyncQueueItem(
            operation=SyncOperation(operation),
            entity_type=SyncEntityType(entity_type),
            entity_id=UUID(entity_id),
            payload=payload,
        )
        self._queue.append(item)
        return item

    def get_queue(self) -> list[SyncQueueItem]:
        """Get all pending queue items."""
        return [item for item in self._queue if item.status == SyncStatus.PENDING]

    def get_status(self) -> dict:
        """Get sync status."""
        pending = sum(1 for i in self._queue if i.status == SyncStatus.PENDING)
        processing = sum(1 for i in self._queue if i.status == SyncStatus.PROCESSING)
        failed = sum(1 for i in self._queue if i.status == SyncStatus.FAILED)

        return {
            "is_online": self._is_online,
            "queue_size": pending,
            "processing": processing,
            "failed": failed,
            "total": len(self._queue),
        }

    def process_queue(self) -> dict:
        """Process the sync queue."""
        if not self._is_online:
            return {"processed": 0, "failed": 0, "message": "Offline"}

        if not self._github_adapter:
            return {"processed": 0, "failed": 0, "message": "No GitHub adapter"}

        processed = 0
        failed = 0
        items = self.get_queue()[: self._batch_size]

        for item in items:
            item.status = SyncStatus.PROCESSING

            try:
                self._process_item(item)
                item.status = SyncStatus.COMPLETED
                self._queue.remove(item)
                processed += 1
            except Exception as e:
                item.retry_count += 1
                item.last_error = str(e)
                if item.retry_count >= 3:
                    item.status = SyncStatus.FAILED
                else:
                    item.status = SyncStatus.PENDING
                    time.sleep(self._retry_delay * (2**item.retry_count))
                failed += 1

        return {"processed": processed, "failed": failed}

    def _process_item(self, item: SyncQueueItem) -> None:
        """Process a single sync item."""
        if item.entity_type == SyncEntityType.ISSUE:
            self._process_issue(item)
        elif item.entity_type == SyncEntityType.COMMENT:
            self._process_comment(item)
        elif item.entity_type == SyncEntityType.LABEL:
            self._process_label(item)

    def _process_issue(self, item: SyncQueueItem) -> None:
        """Process an issue sync item."""
        if item.operation == SyncOperation.CREATE:
            self._github_adapter.create_issue(
                title=item.payload.get("title", ""),
                body=item.payload.get("description", ""),
                labels=item.payload.get("labels", []),
            )
        elif item.operation == SyncOperation.UPDATE:
            self._github_adapter.update_issue(
                issue_number=item.payload.get("github_issue_number"),
                title=item.payload.get("title"),
                body=item.payload.get("description"),
                state=item.payload.get("state"),
            )

    def _process_comment(self, item: SyncQueueItem) -> None:
        """Process a comment sync item."""
        pass

    def _process_label(self, item: SyncQueueItem) -> None:
        """Process a label sync item."""
        pass

    def force_sync(self) -> dict:
        """Force a sync attempt."""
        self.check_connectivity()
        return self.process_queue()

    def clear_completed(self) -> int:
        """Clear completed items from queue."""
        before = len(self._queue)
        self._queue = [i for i in self._queue if i.status != SyncStatus.COMPLETED]
        return before - len(self._queue)


_sync_engine: OfflineFirstSyncEngine | None = None


def get_sync_engine() -> OfflineFirstSyncEngine:
    """Get the global sync engine instance."""
    global _sync_engine
    if _sync_engine is None:
        batch_size = int(os.environ.get("SYNC_BATCH_SIZE", "50"))
        retry_delay = float(os.environ.get("SYNC_RETRY_DELAY", "1.0"))
        _sync_engine = OfflineFirstSyncEngine(batch_size=batch_size, retry_delay=retry_delay)
    return _sync_engine
