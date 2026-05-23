import json

from socialseed_tasker.observability.logging import configure_root_logger, get_logger


def test_json_log_shape(capsys):
    configure_root_logger(level="INFO")
    logger = get_logger("test.logger")
    logger.info("hello world", extra={"foo": "bar"})
    captured = capsys.readouterr()
    out = captured.out.strip()
    j = json.loads(out)
    assert "timestamp" in j
    assert j["level"] == "INFO"
    assert j["logger"] == "test.logger"
    assert j["message"] == "hello world"
    assert j["foo"] == "bar"
