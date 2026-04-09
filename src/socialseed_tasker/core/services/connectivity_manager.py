"""Connectivity manager and priority sync queue.

Monitors network status and manages priority-based sync queue
with metrics tracking.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ConnectionState(str, Enum):
    """Connection state machine states."""

    ONLINE = "online"
    OFFLINE = "offline"
    RECONNECTING = "reconnecting"


class QueuePriority(str, Enum):
    """Priority levels for sync queue items."""

    CRITICAL = "critical"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class PriorityQueueItem:
    """A sync queue item with priority."""

    id: str
    operation: str
    entity_type: str
    entity_id: str
    payload: dict
    priority: QueuePriority = QueuePriority.NORMAL
    created_at: datetime = field(default_factory=_now)
    retry_count: int = 0
    status: str = "pending"
    last_error: str | None = None


class ConnectivityManager:
    """Manages network connectivity and triggers callbacks on state changes."""

    def __init__(
        self,
        check_url: str = "https://api.github.com",
        check_interval: int = 30,
        max_reconnect_delay: int = 300,
    ) -> None:
        self._check_url = check_url
        self._check_interval = check_interval
        self._max_reconnect_delay = max_reconnect_delay
        self._state = ConnectionState.ONLINE
        self._latency: float = 0.0
        self._last_check: datetime | None = None
        self._reconnect_attempts: int = 0
        self._on_connect_callbacks: list[Callable] = []
        self._on_disconnect_callbacks: list[Callable] = []

    def is_online(self) -> bool:
        """Check if currently online."""
        return self._state == ConnectionState.ONLINE

    def get_state(self) -> ConnectionState:
        """Get current connection state."""
        return self._state

    def get_latency(self) -> float:
        """Get last measured latency in seconds."""
        return self._latency

    def check_connectivity(self) -> bool:
        """Check connectivity and update state."""
        import httpx

        try:
            start = time.time()
            response = httpx.get(self._check_url, timeout=5.0)
            self._latency = time.time() - start

            was_offline = self._state != ConnectionState.ONLINE
            self._state = ConnectionState.ONLINE
            self._last_check = _now()
            self._reconnect_attempts = 0

            if was_offline:
                for callback in self._on_connect_callbacks:
                    callback()

            return response.status_code < 500

        except Exception:
            if self._state == ConnectionState.ONLINE:
                self._state = ConnectionState.OFFLINE
                for callback in self._on_disconnect_callbacks:
                    callback()
            self._last_check = _now()
            return False

    def on_connect(self, callback: Callable) -> None:
        """Register a callback for when connection is restored."""
        self._on_connect_callbacks.append(callback)

    def on_disconnect(self, callback: Callable) -> None:
        """Register a callback for when connection is lost."""
        self._on_disconnect_callbacks.append(callback)

    def get_reconnect_delay(self) -> int:
        """Get the current reconnect delay with exponential backoff."""
        delay = min(2**self._reconnect_attempts, self._max_reconnect_delay)
        return delay

    def record_reconnect_attempt(self) -> None:
        """Record a reconnection attempt."""
        self._reconnect_attempts += 1
        self._state = ConnectionState.RECONNECTING


class PrioritySyncQueue:
    """Priority-based sync queue with metrics."""

    def __init__(self) -> None:
        self._queues: dict[QueuePriority, list[PriorityQueueItem]] = {
            QueuePriority.CRITICAL: [],
            QueuePriority.NORMAL: [],
            QueuePriority.LOW: [],
        }
        self._metrics: dict = {
            "total_enqueued": 0,
            "total_processed": 0,
            "total_failed": 0,
            "total_sync_time": 0.0,
        }

    def enqueue(
        self,
        operation: str,
        entity_type: str,
        entity_id: str,
        payload: dict,
        priority: QueuePriority = QueuePriority.NORMAL,
    ) -> PriorityQueueItem:
        """Add an item to the priority queue."""
        item = PriorityQueueItem(
            id=f"{entity_type}_{entity_id}_{int(time.time())}",
            operation=operation,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
            priority=priority,
        )

        self._queues[priority].append(item)
        self._metrics["total_enqueued"] += 1

        return item

    def dequeue(self) -> PriorityQueueItem | None:
        """Get the next item from the queue (highest priority first)."""
        for priority in [QueuePriority.CRITICAL, QueuePriority.NORMAL, QueuePriority.LOW]:
            if self._queues[priority]:
                return self._queues[priority].pop(0)
        return None

    def get_queue_size(self, priority: QueuePriority | None = None) -> int:
        """Get queue size, optionally filtered by priority."""
        if priority:
            return len(self._queues[priority])
        return sum(len(q) for q in self._queues.values())

    def get_failed_items(self) -> list[PriorityQueueItem]:
        """Get all failed items for retry."""
        failed = []
        for queue in self._queues.values():
            for item in queue:
                if item.status == "failed" and item.retry_count < 3:
                    failed.append(item)
        return failed

    def record_success(self, sync_time: float) -> None:
        """Record a successful sync."""
        self._metrics["total_processed"] += 1
        self._metrics["total_sync_time"] += sync_time

    def record_failure(self) -> None:
        """Record a failed sync."""
        self._metrics["total_failed"] += 1

    def get_metrics(self) -> dict:
        """Get queue metrics."""
        avg_sync_time = 0.0
        if self._metrics["total_processed"] > 0:
            avg_sync_time = self._metrics["total_sync_time"] / self._metrics["total_processed"]

        return {
            "queue_size": self.get_queue_size(),
            "critical_size": self.get_queue_size(QueuePriority.CRITICAL),
            "normal_size": self.get_queue_size(QueuePriority.NORMAL),
            "low_size": self.get_queue_size(QueuePriority.LOW),
            "total_enqueued": self._metrics["total_enqueued"],
            "total_processed": self._metrics["total_processed"],
            "total_failed": self._metrics["total_failed"],
            "avg_sync_time": avg_sync_time,
            "failure_rate": (self._metrics["total_failed"] / max(1, self._metrics["total_processed"])),
        }

    def clear(self) -> None:
        """Clear all queues."""
        for queue in self._queues.values():
            queue.clear()


_connectivity_manager: ConnectivityManager | None = None
_priority_sync_queue: PrioritySyncQueue | None = None


def get_connectivity_manager() -> ConnectivityManager:
    """Get the global connectivity manager instance."""
    global _connectivity_manager
    if _connectivity_manager is None:
        check_url = os.environ.get("CONNECTIVITY_CHECK_URL", "https://api.github.com")
        check_interval = int(os.environ.get("CONNECTIVITY_CHECK_INTERVAL", "30"))
        _connectivity_manager = ConnectivityManager(
            check_url=check_url,
            check_interval=check_interval,
        )
    return _connectivity_manager


def get_priority_sync_queue() -> PrioritySyncQueue:
    """Get the global priority sync queue instance."""
    global _priority_sync_queue
    if _priority_sync_queue is None:
        _priority_sync_queue = PrioritySyncQueue()
    return _priority_sync_queue
