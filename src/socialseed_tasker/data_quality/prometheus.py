from __future__ import annotations

import json
from typing import Any

from socialseed_tasker.application.ports import StoragePort


class MetricsStore:
    KEY = "dq:metrics"

    def __init__(self, storage: StoragePort):
        self.storage = storage

    def get_metrics(self) -> dict[Any, Any]:
        raw = self.storage.get(self.KEY) or b"{}"
        try:
            return json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            return {}

    def set_metrics(self, metrics: dict[Any, Any]) -> Any:
        self.storage.put(self.KEY, json.dumps(metrics).encode("utf-8"))
