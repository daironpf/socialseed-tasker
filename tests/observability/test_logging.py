import io
import json
import logging

from socialseed_tasker.observability.logging import JsonFormatter, get_logger


def test_json_log_shape():
    root = logging.getLogger()
    old_handlers = root.handlers[:]
    root.handlers.clear()
    buf = io.StringIO()
    handler = logging.StreamHandler(stream=buf)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel("INFO")
    logger = get_logger("test.logger")
    logger.info("hello world", extra={"foo": "bar"})
    out = buf.getvalue().strip()
    j = json.loads(out)
    assert "timestamp" in j
    assert j["level"] == "INFO"
    assert j["logger"] == "test.logger"
    assert j["message"] == "hello world"
    assert j["foo"] == "bar"
    root.handlers.clear()
    for h in old_handlers:
        root.addHandler(h)
