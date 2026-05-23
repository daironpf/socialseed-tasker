from __future__ import annotations

import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Optional


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extras = {k: v for k, v in record.__dict__.items() if k not in logging.LogRecord.__dict__}
        for k in ("msg", "args", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"):
            extras.pop(k, None)
        if extras:
            payload.update(extras)
        return json.dumps(payload, ensure_ascii=False)


def configure_root_logger(level: str | int = None) -> None:
    level = level or os.getenv("TASKER_LOG_LEVEL", "INFO")
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(level)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)


def get_logger(name: str, trace_id: Optional[str] = None) -> logging.Logger:
    configure_root_logger()
    logger = logging.getLogger(name)

    class _Adapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            extra = kwargs.get("extra", {})
            if trace_id:
                extra = {**extra, "trace_id": trace_id}
            kwargs["extra"] = extra
            return msg, kwargs

    return _Adapter(logger, {})
