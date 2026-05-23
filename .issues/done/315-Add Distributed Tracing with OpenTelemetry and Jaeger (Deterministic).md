### Issue 315 — Add Distributed Tracing with OpenTelemetry and Jaeger (Deterministic)

**Short description**  
Add deterministic, end‑to‑end distributed tracing to Tasker using OpenTelemetry. Instrument HTTP API, background workers, and key libraries (storage, graph operations) to emit spans and traces. Provide a Jaeger backend via Docker Compose for local development and CI, deterministic sampling and resource attributes, automatic context propagation for Celery tasks and HTTP calls, unit and integration tests that assert traces are emitted, and documentation. All file paths, exact code, environment variables, tests, Docker Compose, commands, and PR text are explicit so an autonomous agent or engineer can implement and verify without guessing.

---

## Objective (what the agent must deliver)
1. Add OpenTelemetry instrumentation helpers and a deterministic tracer provider configuration at `tasker/observability/tracing.py`.
2. Instrument FastAPI app, Celery worker entrypoint, Memory/Redis storage adapters, EventBus publish, and DeliveryWorker enqueue/attempt to create spans.
3. Provide a Jaeger backend via `docker-compose.tracing.yml` with deterministic ports and healthchecks.
4. Add a lightweight in‑process test exporter for unit tests to capture spans (`tasker/observability/test_exporter.py`) and utilities to assert spans in tests.
5. Add unit tests:
   - `tests/observability/test_tracing_unit.py` — verifies spans created for API request and storage operations using TestClient and in‑process test exporter.
6. Add integration test:
   - `tests/integration/test_tracing_integration.py` — runs Jaeger via Docker Compose, sends a request to API that triggers a Celery task and storage writes, then queries Jaeger HTTP API to assert a trace exists (skipped unless `TASKER_INTEGRATION=1`).
7. Add documentation `tasker/observability/TRACING.md` describing configuration, how to view traces in Jaeger, and how to enable/disable tracing.
8. Wire tracing initialization in `tasker/cli/wiring.py` and `tasker/workers/worker.py` so tracing starts when container/app/worker starts.
9. Create branch `feature/tracing-opentelemetry-jaeger` and open a PR with the exact PR body provided below.

---

## Why this must be done exactly this way
- OpenTelemetry is vendor‑neutral and allows deterministic instrumentation across services.
- Jaeger is a lightweight, reproducible backend for local development and CI.
- Deterministic sampling and resource attributes ensure reproducible traces for tests.
- Explicit file names, env vars, and tests allow automated agents to implement and verify the feature reliably.

---

## Files to add or modify (exact paths)

- `tasker/observability/tracing.py` **(new)**
- `tasker/observability/test_exporter.py` **(new)**
- `tasker/observability/TRACING.md` **(new)**
- Modify `tasker/api/app.py` to initialize tracing and instrument FastAPI (exact snippet provided below)
- Modify `tasker/workers/worker.py` to initialize tracing in worker process (exact snippet provided below)
- Modify `tasker/infrastructure/memory_storage.py` and `tasker/infrastructure/redis_storage.py` to add spans around `put`, `get`, `delete` (exact snippet provided below)
- Modify `tasker/events/delivery.py` and `tasker/events/bus.py` to add spans for enqueue and publish (exact snippet provided below)
- `docker-compose.tracing.yml` **(new)**
- `tests/observability/test_tracing_unit.py` **(new)**
- `tests/integration/test_tracing_integration.py` **(new, integration)**

---

## Exact code to add

### `tasker/observability/tracing.py`
Create this file with the exact content below.

```python
# tasker/observability/tracing.py
from __future__ import annotations
import os
from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.celery import CeleryInstrumentor

# Deterministic defaults
OTEL_SERVICE_NAME = os.getenv("TASKER_OTEL_SERVICE", "tasker")
OTEL_JAEGER_HOST = os.getenv("TASKER_JAEGER_HOST", "localhost")
OTEL_JAEGER_PORT = int(os.getenv("TASKER_JAEGER_PORT", "6831"))
OTEL_SAMPLING_RATE = float(os.getenv("TASKER_OTEL_SAMPLING_RATE", "1.0"))  # 1.0 = always sample in dev

_tracer_initialized = False

def init_tracing(app=None, celery_app=None, service_name: Optional[str] = None):
    """
    Initialize OpenTelemetry tracing with Jaeger exporter and deterministic sampling.
    If app is provided, FastAPI instrumentation will be applied.
    If celery_app is provided, Celery instrumentation will be applied.
    """
    global _tracer_initialized
    if _tracer_initialized:
        return
    svc = service_name or OTEL_SERVICE_NAME
    resource = Resource.create({"service.name": svc})
    # deterministic sampler: TraceIdRatioBased with configured rate
    sampler = sampling.TraceIdRatioBased(OTEL_SAMPLING_RATE)
    provider = TracerProvider(resource=resource, sampler=sampler)
    trace.set_tracer_provider(provider)
    # Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name=OTEL_JAEGER_HOST,
        agent_port=OTEL_JAEGER_PORT,
    )
    provider.add_span_processor(BatchSpanProcessor(jaeger_exporter))
    # Console exporter for local debugging if env var set
    if os.getenv("TASKER_OTEL_CONSOLE", "0") == "1":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    # instrument requests library for HTTP client spans
    RequestsInstrumentor().instrument()
    # instrument celery if provided
    if celery_app is not None:
        CeleryInstrumentor().instrument()
    # instrument FastAPI app if provided
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
    _tracer_initialized = True

def get_tracer(name: str = "tasker"):
    return trace.get_tracer(name)
```

**Notes**
- This file uses `opentelemetry` packages and Jaeger exporter. Tests will use a test exporter instead of Jaeger.

---

### `tasker/observability/test_exporter.py`
Create this file with the exact content below.

```python
# tasker/observability/test_exporter.py
from __future__ import annotations
from typing import List
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, InMemorySpanExporter
from opentelemetry import trace

class InMemoryTracing:
    """
    Helper to capture spans in unit tests.
    Usage:
      mem = InMemoryTracing()
      mem.start()
      ... run code that creates spans ...
      spans = mem.get_finished_spans()
      mem.stop()
    """

    def __init__(self):
        self.exporter = InMemorySpanExporter()
        self.provider = TracerProvider()
        self.processor = SimpleSpanProcessor(self.exporter)

    def start(self):
        self.provider.add_span_processor(self.processor)
        trace.set_tracer_provider(self.provider)

    def stop(self):
        # reset provider to default
        trace.set_tracer_provider(TracerProvider())

    def get_finished_spans(self) -> List:
        return self.exporter.get_finished_spans()
```

---

### Instrument FastAPI app (`tasker/api/app.py`) — exact snippets

**At top imports** (add these imports):

```python
from tasker.observability.tracing import init_tracing, get_tracer
```

**In startup event or app creation** (insert exactly after `app = FastAPI(...)` or in `@app.on_event("startup")`):

```python
# initialize tracing for API
try:
    init_tracing(app=app, service_name=os.getenv("TASKER_OTEL_SERVICE", "tasker-api"))
except Exception:
    # tracing should not crash the app if unavailable
    pass
tracer = get_tracer("tasker.api")
```

**Wrap request handlers or use instrumentation already applied by FastAPIInstrumentor** — no further code required for automatic instrumentation, but add manual spans in critical handlers where helpful. Example in `create_issue` handler (wrap around usecase call):

```python
from opentelemetry.trace import SpanKind

# inside create_issue endpoint before calling usecase
with tracer.start_as_current_span("create_issue.usecase", kind=SpanKind.INTERNAL):
    usecase(issue=issue)
```

Add similar `with tracer.start_as_current_span(...)` blocks in other heavy endpoints (parse, enqueue task, calculate impact).

---

### Instrument Celery worker (`tasker/workers/worker.py`) — exact snippet

**At top imports** (add):

```python
from tasker.observability.tracing import init_tracing, get_tracer
```

**In `main()` before starting worker** (insert):

```python
# initialize tracing for worker process
try:
    init_tracing(celery_app=None, service_name=os.getenv("TASKER_OTEL_SERVICE", "tasker-worker"))
except Exception:
    pass
worker_tracer = get_tracer("tasker.worker")
```

**Note**: CeleryInstrumentor is invoked by `init_tracing` when a Celery app is passed; if Celery app is created elsewhere, ensure `CeleryInstrumentor().instrument()` is called during worker startup.

---

### Instrument storage adapters

**Memory storage (`tasker/infrastructure/memory_storage.py`)** — add tracer usage in methods. Insert at top:

```python
from tasker.observability.tracing import get_tracer
_tracer = get_tracer("tasker.memory_storage")
```

Wrap methods `put`, `get`, `delete` with spans. Example for `put`:

```python
def put(self, key: str, value: bytes, ttl_seconds: Optional[int] = None) -> None:
    with _tracer.start_as_current_span("memory.put"):
        expire = None
        if ttl_seconds is not None:
            expire = time.time() + float(ttl_seconds)
        with self._lock:
            self._store[key] = (value, expire)
```

Apply analogous spans in `get` and `delete`.

**Redis storage (`tasker/infrastructure/redis_storage.py`)** — add tracer usage similarly. Insert at top:

```python
from tasker.observability.tracing import get_tracer
_tracer = get_tracer("tasker.redis_storage")
```

Wrap `put`, `get`, `delete` with spans named `redis.put`, `redis.get`, `redis.delete`.

---

### Instrument EventBus and DeliveryWorker

**EventBus (`tasker/events/bus.py`)** — add tracer at top:

```python
from tasker.observability.tracing import get_tracer
_tracer = get_tracer("tasker.eventbus")
```

Wrap `publish` handler invocation with a span:

```python
def publish(self, event: EventDTO) -> None:
    with _tracer.start_as_current_span("event.publish"):
        # publish to exact type and wildcard subscribers
        with self._lock:
            handlers = list(self._subs.get(event.type, [])) + list(self._subs.get("*", []))
        for h in handlers:
            try:
                h(event)
            except Exception:
                pass
```

**DeliveryWorker (`tasker/events/delivery.py`)** — add tracer at top:

```python
from tasker.observability.tracing import get_tracer
_tracer = get_tracer("tasker.delivery")
```

Wrap `enqueue_delivery` and `_attempt_delivery` with spans:

```python
def enqueue_delivery(...):
    with _tracer.start_as_current_span("delivery.enqueue"):
        # existing code

def _attempt_delivery(...):
    with _tracer.start_as_current_span("delivery.attempt"):
        # existing code
```

---

### Jaeger Docker Compose (`docker-compose.tracing.yml`)
Create this file at repo root with the exact content below.

```yaml
version: "3.8"
services:
  jaeger:
    image: jaegertracing/all-in-one:1.49
    container_name: tasker-jaeger
    ports:
      - "16686:16686"   # UI
      - "6831:6831/udp" # agent
      - "14268:14268"   # collector
    environment:
      COLLECTOR_ZIPKIN_HTTP_PORT: 9411
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:16686/ || exit 1"]
      interval: 5s
      timeout: 5s
      retries: 12
```

**Notes**
- Jaeger UI available at `http://localhost:16686`.

---

## Tests to add

### Unit test: `tests/observability/test_tracing_unit.py`
Create this file with the exact content below.

```python
# tests/observability/test_tracing_unit.py
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from tasker.observability.test_exporter import InMemoryTracing
from tasker.api.app import app
import time

def test_api_request_creates_spans():
    mem = InMemoryTracing()
    mem.start()
    client = TestClient(app)
    # call a simple endpoint that triggers storage operations
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    spans = mem.get_finished_spans()
    # expect at least one span for the request and one for storage get/put if instrumented
    assert any("http" in s.name.lower() or "request" in s.name.lower() for s in spans)
    mem.stop()
```

### Integration test: `tests/integration/test_tracing_integration.py`
Create this file with the exact content below.

```python
# tests/integration/test_tracing_integration.py
import os
import time
import requests
import pytest

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration disabled")

JAEGER_UI = os.getenv("TASKER_JAEGER_URL", "http://localhost:16686")

def wait_for_jaeger(timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{JAEGER_UI}/api/services", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def test_trace_emitted_and_visible():
    _skip_if_not_integration()
    assert wait_for_jaeger(), "Jaeger not ready"
    # send a request that triggers a trace
    r = requests.get("http://localhost:8000/api/v1/health", timeout=5)
    assert r.status_code == 200
    # give Jaeger some time to ingest
    time.sleep(2)
    # query Jaeger services
    r2 = requests.get(f"{JAEGER_UI}/api/services", timeout=5)
    assert r2.status_code == 200
    services = r2.json()
    # our service name should be present
    assert any("tasker" in s for s in services)
```

---

## Documentation

### `tasker/observability/TRACING.md`
Create this file with the exact content below.

```
OpenTelemetry Tracing and Jaeger

Overview
- Tracing is configured in tasker/observability/tracing.py.
- Default service name: TASKER_OTEL_SERVICE (env var).
- Jaeger agent host/port configurable via TASKER_JAEGER_HOST and TASKER_JAEGER_PORT.

Local development
1. Start Jaeger:
   docker compose -f docker-compose.tracing.yml up -d
2. Start API and worker stacks (ensure TASKER_JAEGER_HOST points to host where Jaeger agent is reachable).
3. Open Jaeger UI: http://localhost:16686 and search for service "tasker" or "tasker-api".

Environment variables
- TASKER_OTEL_SERVICE default "tasker"
- TASKER_JAEGER_HOST default "localhost"
- TASKER_JAEGER_PORT default "6831"
- TASKER_OTEL_SAMPLING_RATE default "1.0" (1.0 = sample all traces)
- TASKER_OTEL_CONSOLE set to "1" to also print spans to console

Testing
- Unit tests use an in-memory exporter (tasker/observability/test_exporter.py).
- Integration tests query Jaeger HTTP API; set TASKER_INTEGRATION=1 to enable.

Notes
- Tracing initialization is safe to call multiple times; it is idempotent.
- In production, configure sampling and exporter according to scale and privacy requirements.
```

---

## Wiring changes

Modify `tasker/cli/wiring.py` to call `init_tracing()` during container build/startup. Insert the following excerpt in `build_default_container()` after container creation or before returning:

```python
# initialize tracing for container processes (best-effort)
try:
    from tasker.observability.tracing import init_tracing
    init_tracing(service_name=os.getenv("TASKER_OTEL_SERVICE", "tasker"))
except Exception:
    pass
```

Also ensure worker startup calls `init_tracing` as shown earlier.

---

## Exact commands the agent must run

```bash
git checkout -b feature/tracing-opentelemetry-jaeger
# create files as specified
python -m pip install -e .
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi opentelemetry-instrumentation-requests opentelemetry-exporter-jaeger opentelemetry-instrumentation-celery
# run unit tests
pytest tests/observability/test_tracing_unit.py -q
# optional: run Jaeger and integration test
docker compose -f docker-compose.tracing.yml up -d
export TASKER_INTEGRATION=1
pytest tests/integration/test_tracing_integration.py -q -m integration || true
# commit and push
git add tasker/observability tasker/api/app.py tasker/workers/worker.py tasker/infrastructure tasker/events docker-compose.tracing.yml tests/observability tests/integration
git commit -m "feat(tracing): add OpenTelemetry instrumentation and Jaeger backend with tests"
git push origin feature/tracing-opentelemetry-jaeger
```

---

## PR body exact text to paste

```
Summary:
- Added OpenTelemetry tracing initialization at tasker/observability/tracing.py with deterministic sampling and Jaeger exporter.
- Instrumented FastAPI, Celery worker, storage adapters, EventBus and DeliveryWorker to emit spans.
- Added Jaeger Docker Compose file docker-compose.tracing.yml for local development.
- Added in-memory test exporter helper tasker/observability/test_exporter.py and unit/integration tests.
- Wired tracing initialization into container and worker startup.
- Added documentation tasker/observability/TRACING.md.

Verification steps executed by this agent:
1. Installed package in editable mode and required OpenTelemetry packages.
2. Ran unit tests that use in-memory exporter to assert spans are created.
3. Optionally started Jaeger via docker compose and ran integration test to assert traces are visible in Jaeger.

Files changed:
- tasker/observability/tracing.py
- tasker/observability/test_exporter.py
- tasker/observability/TRACING.md
- Modified: tasker/api/app.py, tasker/workers/worker.py, tasker/infrastructure/*, tasker/events/*
- docker-compose.tracing.yml
- tests/observability/test_tracing_unit.py
- tests/integration/test_tracing_integration.py

Notes:
- Tracing is enabled by default in development with sampling rate 1.0. Adjust TASKER_OTEL_SAMPLING_RATE in env for production.
- Jaeger is used for local development only; production should use a managed tracing backend or OTLP collector.
```

---

## Acceptance criteria (must be satisfied exactly)
- `tasker/observability/tracing.py` exists and initializes OpenTelemetry with Jaeger exporter and deterministic sampling.
- FastAPI app and worker initialize tracing on startup.
- Storage adapters, EventBus, and DeliveryWorker create spans for key operations.
- `docker-compose.tracing.yml` exists and starts Jaeger on ports `16686` and `6831` with healthcheck.
- Unit test `tests/observability/test_tracing_unit.py` exists and passes using in-memory exporter.
- Integration test `tests/integration/test_tracing_integration.py` exists and passes when Jaeger is available via `docker-compose.tracing.yml` and `TASKER_INTEGRATION=1`.
- `tasker/observability/TRACING.md` documents configuration and usage.
- Branch `feature/tracing-opentelemetry-jaeger` created and PR opened with the exact PR body above.

---

## Labels to apply on GitHub
- `observability`
- `tracing`
- `opentelemetry`
- `integration-test`
- `medium-priority`

---

## Estimated effort
**Small–Medium (S–M)** — expected to take **1–3 hours** depending on environment and package installation.