"""Error observability: unhandled 500s must leave full tracebacks in logs (issue #594).

Before this fix ``generic_error_handler`` returned the INTERNAL_ERROR envelope
but never called ``logger.exception`` and ``JsonFormatter`` discarded
``exc_info`` — diagnosing any 500 required in-process repro scripts.
"""

from __future__ import annotations

import io
import json
import logging

from fastapi.testclient import TestClient

from socialseed_tasker.infrastructure.web_api.app import create_app
from socialseed_tasker.observability.logging import JsonFormatter

APP_LOGGER = "socialseed_tasker.infrastructure.web_api.app"


def _client() -> TestClient:
    app = create_app(repository=None)

    @app.get("/boom-594")
    async def boom() -> None:
        raise RuntimeError("kaboom-594")

    return TestClient(app, raise_server_exceptions=False)


def test_unhandled_exception_returns_envelope_without_internals() -> None:
    client = _client()
    resp = client.get("/boom-594")

    assert resp.status_code == 500
    body = resp.json()
    assert body["error"]["code"] == "INTERNAL_ERROR"
    assert body["error"]["message"] == "An unexpected error occurred"
    assert body["error"]["details"]["detail"] is None
    assert body["meta"]["request_id"]


def test_unhandled_exception_logs_traceback_with_request_id(caplog) -> None:
    client = _client()
    with caplog.at_level(logging.ERROR, logger=APP_LOGGER):
        resp = client.get("/boom-594")

    request_id = resp.json()["meta"]["request_id"]
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR and r.name == APP_LOGGER]
    assert error_records, "expected an ERROR record for the unhandled exception"

    record = error_records[0]
    message = record.getMessage()
    assert "unhandled error" in message
    assert "GET" in message
    assert "/boom-594" in message
    assert request_id in message
    assert "RuntimeError" in message

    assert record.exc_info is not None
    assert record.exc_info[0] is RuntimeError


def test_json_formatter_renders_traceback_as_exception_field() -> None:
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("test.jsonfmt.594")
    logger.handlers = [handler]
    logger.setLevel(logging.ERROR)
    logger.propagate = False

    try:
        raise RuntimeError("kaboom-594")
    except RuntimeError:
        logger.exception("unhandled error on GET /boom-594 (request_id=%s)", "rid-594")

    payload = json.loads(stream.getvalue())
    assert payload["level"] == "ERROR"
    assert "rid-594" in payload["message"]
    assert "RuntimeError: kaboom-594" in payload["exception"]
    assert 'File "' in payload["exception"]


def test_http_4xx_not_logged_as_error(caplog) -> None:
    client = _client()
    with caplog.at_level(logging.ERROR):
        resp = client.get("/does-not-exist-594")

    assert resp.status_code == 404
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR and r.name == APP_LOGGER]
    assert error_records == []


def test_value_error_4xx_not_logged_as_error(caplog) -> None:
    app = create_app(repository=None)

    @app.get("/bad-value-594")
    async def bad_value() -> None:
        raise ValueError("controlled 4xx")

    client = TestClient(app, raise_server_exceptions=False)
    with caplog.at_level(logging.ERROR):
        resp = client.get("/bad-value-594")

    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "VALIDATION_ERROR"
    error_records = [r for r in caplog.records if r.levelno >= logging.ERROR and r.name == APP_LOGGER]
    assert error_records == []
