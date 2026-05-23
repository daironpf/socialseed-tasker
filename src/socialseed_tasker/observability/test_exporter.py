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
        self.processor = SimpleSpanProcessor(self.exporter)
        self._previous_provider = None

    def start(self):
        existing = trace.get_tracer_provider()
        if isinstance(existing, TracerProvider):
            existing.add_span_processor(self.processor)
        else:
            self._previous_provider = existing
            provider = TracerProvider()
            provider.add_span_processor(self.processor)
            try:
                trace.set_tracer_provider(provider)
            except Exception:
                pass

    def stop(self):
        pass

    def get_finished_spans(self) -> List:
        return self.exporter.get_finished_spans()
