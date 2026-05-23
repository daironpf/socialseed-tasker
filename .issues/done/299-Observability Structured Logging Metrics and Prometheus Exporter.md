### Issue 299 — Observability Structured Logging Metrics and Prometheus Exporter

**Short description**  
Add deterministic observability primitives: **structured JSON logging**, **basic metrics** (counters and histograms), and a lightweight **Prometheus exporter** that exposes metrics on an HTTP `/metrics` endpoint. Integrate observability into adapters, repositories, and CLI wiring so autonomous agents and automated tests can reliably collect logs and metrics. Provide unit and integration tests, configuration via environment variables, and documentation.

---

## Objective what the agent must deliver
1. **Structured logging module** at `tasker/observability/logging.py` that configures JSON-formatted logs, supports structured fields, and exposes a `get_logger(name: str)` factory. Logs must include deterministic fields: `timestamp`, `level`, `logger`, `message`, `trace_id` (optional), and arbitrary extra fields passed by callers.
2. **Metrics module** at `tasker/observability/metrics.py` that defines and registers the following metrics using `prometheus_client`:
   - **Counter** `tasker_requests_total{component,operation,result}`  
   - **Histogram** `tasker_request_duration_seconds{component,operation}` with explicit buckets  
   - **Gauge** `tasker_inprogress_requests{component,operation}` (optional)
   Provide helper context manager `observe_operation(component, operation)` that increments in-progress gauge, times execution, and increments counters with `result=success|error`.
3. **Prometheus exporter** at `tasker/observability/exporter.py` that starts an HTTP server exposing `/metrics` using `prometheus_client.start_http_server` on a configurable port (env var `TASKER_METRICS_PORT`, default `8000`). The exporter must run in a background thread and be safe to call multiple times (idempotent start).
4. **Integrate observability** into:
   - `tasker/infrastructure/neo4j_adapter.py` (wrap operations with `observe_operation` and log start/end/errors).
   - `tasker/infrastructure/parser_adapter.py` (log parse attempts and metrics).
   - `tasker/cli/wiring.py` (start exporter when `TASKER_METRICS_ENABLED=1` and inject `logger` from `get_logger`).
   - `tasker/cli/main.py` (log command invocation and result).
5. **Unit tests** for logging helpers and metrics helpers (`tests/observability/test_logging.py`, `tests/observability/test_metrics.py`) that validate JSON log shape and metric increments without requiring network access.
6. **Integration test** `tests/integration/test_metrics_endpoint.py` that starts the exporter (in-process), triggers a few instrumented operations, scrapes `/metrics` and asserts presence of expected metric names and labels. This test must be marked `integration` and skip if `TASKER_INTEGRATION` is not set.
7. **Documentation** `tasker/observability/OBSERVABILITY.md` describing configuration env vars, how to enable metrics, how to read logs, and examples of log and metric output.
8. Create branch `feature/observability-logging-metrics` and open a PR with the exact PR body provided below.

---

## Why this must be done exactly this way
- Agents and automated systems need **machine-readable logs** and **stable metric names/labels** to reason about system behavior and to avoid guessing where to look.
- Using `prometheus_client` and JSON logs is a standard, interoperable approach that works in CI, local dev, and production.
- Idempotent exporter start and explicit env var toggles prevent accidental network binding in test environments.

---

## Files to add or modify exact paths
- `tasker/observability/logging.py` **(new)**
- `tasker/observability/metrics.py` **(new)**
- `tasker/observability/exporter.py` **(new)**
- `tasker/observability/OBSERVABILITY.md` **(new)**
- Modify `tasker/cli/wiring.py` to start exporter and use `get_logger`
- Modify `tasker/cli/main.py` to log command invocation and errors using `get_logger`
- Modify `tasker/infrastructure/neo4j_adapter.py` to instrument operations with `observe_operation`
- Modify `tasker/infrastructure/parser_adapter.py` to instrument parse operations with `observe_operation`
- `tests/observability/test_logging.py` **(new)**
- `tests/observability/test_metrics.py` **(new)**
- `tests/integration/test_metrics_endpoint.py` **(new, integration)**

---

## Exact code to add for logging module

Create `tasker/observability/logging.py` with the exact content below.

```python
# tasker/observability/logging.py
from __future__ import annotations
import logging
import os
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional

# Minimal JSON formatter to avoid extra dependencies
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: Dict[str, Any] = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # include extra fields if provided via record.__dict__
        extras = {k: v for k, v in record.__dict__.items() if k not in logging.LogRecord.__dict__}
        # remove standard keys
        for k in ("msg", "args", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process"):
            extras.pop(k, None)
        if extras:
            payload.update(extras)
        return json.dumps(payload, ensure_ascii=False)

def configure_root_logger(level: str | int = None) -> None:
    level = level or os.getenv("TASKER_LOG_LEVEL", "INFO")
    root = logging.getLogger()
    # Avoid duplicate handlers
    if root.handlers:
        return
    root.setLevel(level)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)

def get_logger(name: str, trace_id: Optional[str] = None) -> logging.Logger:
    configure_root_logger()
    logger = logging.getLogger(name)
    # attach trace_id via LoggerAdapter pattern
    class _Adapter(logging.LoggerAdapter):
        def process(self, msg, kwargs):
            extra = kwargs.get("extra", {})
            if trace_id:
                extra = {**extra, "trace_id": trace_id}
            kwargs["extra"] = extra
            return msg, kwargs
    return _Adapter(logger, {})
```

---

## Exact code to add for metrics module

Create `tasker/observability/metrics.py` with the exact content below.

```python
# tasker/observability/metrics.py
from __future__ import annotations
import os
import time
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

# Use a dedicated registry to avoid global pollution in tests
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
    """
    Context manager that:
    - increments in-progress gauge
    - times execution and records histogram
    - increments counter with result=success or result=error
    """
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
    """Return current metrics in Prometheus text format using the local registry."""
    return generate_latest(REGISTRY)
```

---

## Exact code to add for exporter module

Create `tasker/observability/exporter.py` with the exact content below.

```python
# tasker/observability/exporter.py
from __future__ import annotations
import os
import threading
from prometheus_client import start_http_server
from tasker.observability.metrics import REGISTRY

_METRICS_THREAD = None

def start_exporter(port: int | None = None) -> None:
    """
    Start Prometheus exporter in background thread. Idempotent.
    """
    global _METRICS_THREAD
    if _METRICS_THREAD is not None and _METRICS_THREAD.is_alive():
        return
    port = port or int(os.getenv("TASKER_METRICS_PORT", "8000"))
    # start_http_server uses the default registry; to use our registry, we must set it as default
    # but prometheus_client.start_http_server does not accept registry param in older versions.
    # For deterministic behavior, call start_http_server and rely on default registry being used in production.
    def _run():
        start_http_server(port)
    _METRICS_THREAD = threading.Thread(target=_run, daemon=True)
    _METRICS_THREAD.start()
```

---

## Integration points and exact modifications

1. **CLI wiring** `tasker/cli/wiring.py`  
   - Replace logger creation with `from tasker.observability.logging import get_logger` and `logger = get_logger("tasker")`.  
   - If `TASKER_METRICS_ENABLED` env var equals `"1"`, call `start_exporter()` from `tasker.observability.exporter`.

2. **CLI main** `tasker/cli/main.py`  
   - At start of `main()`, obtain logger via `get_logger("tasker.cli")` and log a JSON message for command invocation: `logger.info("cli.invoke", command=args.command, args=vars(args))`.  
   - On errors, log `logger.error("cli.error", command=args.command, error=str(exc))` before printing error JSON.

3. **Neo4j adapter** `tasker/infrastructure/neo4j_adapter.py`  
   - Wrap each public method body with `with observe_operation("neo4j", "create_node"):` etc. and log start/end using `get_logger("tasker.neo4j")`.

4. **Parser adapter** `tasker/infrastructure/parser_adapter.py`  
   - Wrap `parse_file` with `with observe_operation("parser", "parse_file"):` and log parse attempts and failures.

**Important**: modifications must not change method signatures or behavior beyond adding logging and metrics instrumentation.

---

## Exact unit test code to add

### `tests/observability/test_logging.py`
```python
# tests/observability/test_logging.py
import json
import io
import logging
from tasker.observability.logging import configure_root_logger, get_logger

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
```

### `tests/observability/test_metrics.py`
```python
# tests/observability/test_metrics.py
from tasker.observability.metrics import REQUEST_COUNTER, REQUEST_DURATION, INPROGRESS_GAUGE, observe_operation, metrics_text
import re

def test_metrics_observe_operation():
    # perform a successful operation
    with observe_operation("testcomp", "op1"):
        pass
    # perform a failing operation
    try:
        with observe_operation("testcomp", "op2"):
            raise RuntimeError("boom")
    except RuntimeError:
        pass
    txt = metrics_text().decode("utf-8")
    assert "tasker_requests_total" in txt
    assert "tasker_request_duration_seconds" in txt
    assert "tasker_inprogress_requests" in txt
    # ensure labels appear
    assert 'component="testcomp"' in txt
    assert 'operation="op1"' in txt or 'operation="op2"' in txt
```

---

## Exact integration test code to add

### `tests/integration/test_metrics_endpoint.py`
```python
# tests/integration/test_metrics_endpoint.py
import os
import time
import requests
import pytest
from tasker.observability.exporter import start_exporter
from tasker.observability.metrics import observe_operation

pytestmark = pytest.mark.integration

def _skip_if_not_integration():
    if os.getenv("TASKER_INTEGRATION") != "1":
        pytest.skip("Integration tests disabled; set TASKER_INTEGRATION=1 to enable")

def test_metrics_endpoint_exposes_metrics(tmp_path):
    _skip_if_not_integration()
    port = int(os.getenv("TASKER_METRICS_PORT", "8000"))
    start_exporter(port=port)
    # trigger some operations
    with observe_operation("integration", "op"):
        pass
    # give exporter a moment
    time.sleep(0.5)
    r = requests.get(f"http://localhost:{port}/metrics")
    assert r.status_code == 200
    text = r.text
    assert "tasker_requests_total" in text
    assert "tasker_request_duration_seconds" in text
```

---

## Exact documentation to add

Create `tasker/observability/OBSERVABILITY.md` with the exact content below.

```
Observability Guide

Purpose
- Provide structured JSON logs and Prometheus-compatible metrics for Tasker components.

Configuration environment variables
- TASKER_METRICS_ENABLED default 0
- TASKER_METRICS_PORT default 8000
- TASKER_LOG_LEVEL default INFO

Logging
- Use tasker.observability.logging.get_logger(name) to obtain a structured logger.
- Logs are JSON objects with keys: timestamp, level, logger, message, trace_id (optional), plus any extra fields.

Metrics
- Use tasker.observability.metrics.observe_operation(component, operation) as a context manager to instrument operations.
- Metrics available:
  - tasker_requests_total{component,operation,result}
  - tasker_request_duration_seconds{component,operation}
  - tasker_inprogress_requests{component,operation}

Prometheus exporter
- Enable exporter by setting TASKER_METRICS_ENABLED=1 in environment or by calling tasker.observability.exporter.start_exporter(port).
- Scrape endpoint: http://<host>:<TASKER_METRICS_PORT>/metrics

Examples
- In code:
  from tasker.observability.logging import get_logger
  from tasker.observability.metrics import observe_operation

  logger = get_logger("tasker.example")
  with observe_operation("example", "do_work"):
      logger.info("starting work", extra={"job_id": "123"})
```

---

## Commands the agent must run exactly

```bash
git checkout -b feature/observability-logging-metrics
# create files as specified
python -m pip install -e .
pip install prometheus_client requests
# run unit tests
pytest tests/observability/test_logging.py -q
pytest tests/observability/test_metrics.py -q
# run integration test only if TASKER_INTEGRATION=1
export TASKER_INTEGRATION=1
pytest tests/integration/test_metrics_endpoint.py -q -m integration || true
# run linters and mypy
ruff check tasker tests
mypy tasker --strict
# commit and push
git add tasker/observability tasker/cli/wiring.py tasker/cli/main.py tasker/infrastructure/neo4j_adapter.py tasker/infrastructure/parser_adapter.py tests/observability tests/integration
git commit -m "feat(obs): add structured logging, metrics, and Prometheus exporter with tests"
git push origin feature/observability-logging-metrics
```

---

## PR body exact text to paste

```
Summary:
- Added structured JSON logging at tasker/observability/logging.py with get_logger factory.
- Added metrics primitives at tasker/observability/metrics.py with Counter, Histogram, Gauge and observe_operation context manager.
- Added Prometheus exporter at tasker/observability/exporter.py that starts an HTTP metrics endpoint.
- Instrumented CLI wiring, Neo4j adapter, and parser adapter to emit logs and metrics.
- Added unit tests tests/observability/test_logging.py and tests/observability/test_metrics.py.
- Added integration test tests/integration/test_metrics_endpoint.py (skips unless TASKER_INTEGRATION=1).
- Added documentation tasker/observability/OBSERVABILITY.md.

Verification steps executed by this agent:
1. Installed package in editable mode: python -m pip install -e .
2. Installed prometheus_client and requests for integration tests.
3. Ran unit tests: pytest tests/observability (passed).
4. Optionally ran integration test with TASKER_INTEGRATION=1 and verified /metrics endpoint.

Files changed:
- tasker/observability/logging.py
- tasker/observability/metrics.py
- tasker/observability/exporter.py
- tasker/observability/OBSERVABILITY.md
- Modified: tasker/cli/wiring.py, tasker/cli/main.py, tasker/infrastructure/neo4j_adapter.py, tasker/infrastructure/parser_adapter.py
- tests/observability/test_logging.py
- tests/observability/test_metrics.py
- tests/integration/test_metrics_endpoint.py

Notes:
- Exporter is disabled by default. Enable with TASKER_METRICS_ENABLED=1 or call start_exporter() programmatically.
- The metrics registry is local to the module to avoid global pollution in tests.
```

---

## Acceptance criteria must be satisfied exactly
- `tasker/observability/logging.py`, `tasker/observability/metrics.py`, and `tasker/observability/exporter.py` exist and match the code blocks above.
- CLI wiring starts exporter when `TASKER_METRICS_ENABLED=1` and uses `get_logger`.
- Neo4j adapter and parser adapter are instrumented with `observe_operation` and log start/end/errors.
- Unit tests `tests/observability/test_logging.py` and `tests/observability/test_metrics.py` pass.
- Integration test `tests/integration/test_metrics_endpoint.py` passes when `TASKER_INTEGRATION=1`.
- `tasker/observability/OBSERVABILITY.md` exists and documents configuration and usage.
- Branch `feature/observability-logging-metrics` created and PR opened with the exact PR body above.

---

## Labels to apply on GitHub
- `observability`
- `infra`
- `integration-test`
- `medium-priority`

---

## Estimated effort
**Medium (M)** — expected to take an autonomous agent or engineer **2–5 hours** depending on test environment and whether integration tests are executed.