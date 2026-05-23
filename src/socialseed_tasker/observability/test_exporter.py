# src/socialseed_tasker/observability/test_exporter.py
from __future__ import annotations
from typing import List
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult
from opentelemetry import trace


class _InMemoryExporter(SpanExporter):
    def __init__(self):
        self.spans: List[ReadableSpan] = []

    def export(self, spans):
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass

    def get_finished_spans(self) -> List[ReadableSpan]:
        return list(self.spans)


class InMemoryTracing:
    def __init__(self):
        self.exporter = _InMemoryExporter()
        self.provider = TracerProvider()
        self.processor = SimpleSpanProcessor(self.exporter)

    def start(self):
        self.provider.add_span_processor(self.processor)
        trace.set_tracer_provider(self.provider)

    def stop(self):
        from opentelemetry.sdk.trace import _TracerProvider
        if not isinstance(trace.get_tracer_provider(), _TracerProvider):
            trace.set_tracer_provider(TracerProvider())

    def get_finished_spans(self) -> List:
        return self.exporter.get_finished_spans()
