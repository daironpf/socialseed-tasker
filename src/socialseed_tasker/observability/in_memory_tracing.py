# src/socialseed_tasker/observability/in_memory_tracing.py
# In-memory OpenTelemetry helpers (kept out of test collection on purpose).
from __future__ import annotations

import contextlib
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import ReadableSpan, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter, SpanExportResult


class _InMemoryExporter(SpanExporter):
    def __init__(self) -> None:
        self.spans: list[ReadableSpan] = []

    def export(self, spans: Any) -> Any:
        self.spans.extend(spans)
        return SpanExportResult.SUCCESS

    def shutdown(self) -> Any:
        pass

    def get_finished_spans(self) -> list[ReadableSpan]:
        return list(self.spans)


class InMemoryTracing:
    def __init__(self) -> None:
        self.exporter = _InMemoryExporter()
        self.processor = SimpleSpanProcessor(self.exporter)
        self._previous_provider: object | None = None

    def start(self) -> Any:
        existing = trace.get_tracer_provider()
        if isinstance(existing, TracerProvider):
            existing.add_span_processor(self.processor)
        else:
            self._previous_provider = existing
            provider = TracerProvider()
            provider.add_span_processor(self.processor)
            with contextlib.suppress(Exception):
                trace.set_tracer_provider(provider)

    def stop(self) -> Any:
        pass

    def get_finished_spans(self) -> list[Any]:
        return self.exporter.get_finished_spans()
