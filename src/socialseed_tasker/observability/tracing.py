# src/socialseed_tasker/observability/tracing.py
from __future__ import annotations
import os
from typing import Optional

OTEL_SERVICE_NAME = os.getenv("TASKER_OTEL_SERVICE", "tasker")
OTEL_JAEGER_HOST = os.getenv("TASKER_JAEGER_HOST", "localhost")
OTEL_JAEGER_PORT = int(os.getenv("TASKER_JAEGER_PORT", "6831"))
OTEL_SAMPLING_RATE = float(os.getenv("TASKER_OTEL_SAMPLING_RATE", "1.0"))

_tracer_initialized = False

def init_tracing(app=None, celery_app=None, service_name: Optional[str] = None):
    global _tracer_initialized
    if _tracer_initialized:
        return
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider, sampling
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    svc = service_name or OTEL_SERVICE_NAME
    resource = Resource.create({"service.name": svc})
    sampler = sampling.TraceIdRatioBased(OTEL_SAMPLING_RATE)
    provider = TracerProvider(resource=resource, sampler=sampler)
    trace.set_tracer_provider(provider)
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter
        jaeger_exporter = JaegerExporter(
            agent_host_name=OTEL_JAEGER_HOST,
            agent_port=OTEL_JAEGER_PORT,
        )
        provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    except Exception:
        pass
    if os.getenv("TASKER_OTEL_CONSOLE", "0") == "1":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
    except Exception:
        pass
    if celery_app is not None:
        try:
            from opentelemetry.instrumentation.celery import CeleryInstrumentor
            CeleryInstrumentor().instrument()
        except Exception:
            pass
    if app is not None:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument_app(app)
        except Exception:
            pass
    _tracer_initialized = True

def get_tracer(name: str = "tasker"):
    from opentelemetry import trace
    return trace.get_tracer(name)
