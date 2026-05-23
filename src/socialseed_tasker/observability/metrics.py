from __future__ import annotations

import time
from contextlib import contextmanager

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

REGISTRY = CollectorRegistry()

REQUEST_COUNTER = Counter(
    "tasker_requests_total",
    "Total number of tasker operations",
    ["component", "operation", "result"],
    registry=REGISTRY,
)

REQUEST_DURATION = Histogram(
    "tasker_request_duration_seconds",
    "Duration of tasker operations in seconds",
    ["component", "operation"],
    buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0),
    registry=REGISTRY,
)

INPROGRESS_GAUGE = Gauge(
    "tasker_inprogress_requests",
    "Number of in-progress operations",
    ["component", "operation"],
    registry=REGISTRY,
)


@contextmanager
def observe_operation(component: str, operation: str):
    INPROGRESS_GAUGE.labels(component=component, operation=operation).inc()
    start = time.time()
    try:
        yield
        duration = time.time() - start
        REQUEST_DURATION.labels(component=component, operation=operation).observe(duration)
        REQUEST_COUNTER.labels(component=component, operation=operation, result="success").inc()
    except Exception:
        duration = time.time() - start
        REQUEST_DURATION.labels(component=component, operation=operation).observe(duration)
        REQUEST_COUNTER.labels(component=component, operation=operation, result="error").inc()
        raise
    finally:
        INPROGRESS_GAUGE.labels(component=component, operation=operation).dec()


def metrics_text() -> bytes:
    return generate_latest(REGISTRY)
