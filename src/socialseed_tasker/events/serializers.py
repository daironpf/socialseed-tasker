from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class EventDTO:
    id: str
    type: str
    source: str
    payload: dict[str, Any]
    created_at: str

    @staticmethod
    def from_dict(d: dict[str, Any]) -> EventDTO:
        return EventDTO(
            id=d.get("id") or d.get("event_id") or "",
            type=d["type"],
            source=d.get("source", ""),
            payload=d.get("payload", {}),
            created_at=d.get("created_at", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
        )

    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "payload": self.payload,
            "created_at": self.created_at,
        }, ensure_ascii=False)
