from socialseed_tasker.observability.metrics import (
    INPROGRESS_GAUGE,
    REQUEST_COUNTER,
    REQUEST_DURATION,
    metrics_text,
    observe_operation,
)


def test_metrics_observe_operation():
    with observe_operation("testcomp", "op1"):
        pass
    try:
        with observe_operation("testcomp", "op2"):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    txt = metrics_text().decode("utf-8")
    assert "tasker_requests_total" in txt
    assert "tasker_request_duration_seconds" in txt
    assert "tasker_inprogress_requests" in txt
    assert 'component="testcomp"' in txt
    assert 'operation="op1"' in txt or 'operation="op2"' in txt
