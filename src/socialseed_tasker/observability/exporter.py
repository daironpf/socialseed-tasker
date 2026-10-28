from __future__ import annotations

import os
import threading
from typing import Any

from prometheus_client import start_http_server

from socialseed_tasker.observability.metrics import REGISTRY

_METRICS_THREAD = None


def start_exporter(port: int | None = None) -> None:
    global _METRICS_THREAD
    if _METRICS_THREAD is not None and _METRICS_THREAD.is_alive():
        return
    port = port or int(os.getenv("TASKER_METRICS_PORT", "8000"))

    def _run() -> Any:
        start_http_server(port, registry=REGISTRY)

    _METRICS_THREAD = threading.Thread(target=_run, daemon=True)
    _METRICS_THREAD.start()
