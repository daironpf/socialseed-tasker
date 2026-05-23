from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict
import json
from datetime import datetime

@dataclass
class EventDTO:
    id: str
    type: str
    source: str
    payload: Dict[str, Any]
    created_at: str

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "EventDTO":
        return EventDTO(
            id=d.get("id") or d.get("event_id") or "",
            type=d["type"],
            source=d.get("source", ""),
            payload=d.get("payload", {}),
            created_at=d.get("created_at", datetime.utcnow().isoformat() + "Z"),
        )

    def to_json(self) -> str:
        return json.dumps({
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "payload": self.payload,
            "created_at": self.created_at,
        }, ensure_ascii=False)
