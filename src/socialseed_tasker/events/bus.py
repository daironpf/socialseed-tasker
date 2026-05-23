from __future__ import annotations
from typing import Callable, Dict, List
import threading
from socialseed_tasker.events.serializers import EventDTO

Subscriber = Callable[[EventDTO], None]

class EventBus:
    def __init__(self):
        self._subs: Dict[str, List[Subscriber]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_type: str, fn: Subscriber) -> None:
        with self._lock:
            self._subs.setdefault(event_type, []).append(fn)

    def unsubscribe(self, event_type: str, fn: Subscriber) -> None:
        with self._lock:
            if event_type in self._subs:
                self._subs[event_type] = [s for s in self._subs[event_type] if s != fn]

    def publish(self, event: EventDTO) -> None:
        with self._lock:
            handlers = list(self._subs.get(event.type, [])) + list(self._subs.get("*", []))
        for h in handlers:
            try:
                h(event)
            except Exception:
                pass
