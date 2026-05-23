# tests/observability/test_tracing_unit.py
from socialseed_tasker.observability.test_exporter import InMemoryTracing

def test_in_memory_tracing_captures_spans():
    mem = InMemoryTracing()
    mem.start()
    from opentelemetry import trace
    tracer = trace.get_tracer("test")
    with tracer.start_as_current_span("test-span"):
        pass
    spans = mem.get_finished_spans()
    assert len(spans) >= 1
    assert any(s.name == "test-span" for s in spans)
    mem.stop()
