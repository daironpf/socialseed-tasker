Observability Guide

Purpose
- Provide structured JSON logs and Prometheus-compatible metrics for Tasker components.

Configuration environment variables
- TASKER_METRICS_ENABLED default 0
- TASKER_METRICS_PORT default 8000
- TASKER_LOG_LEVEL default INFO

Logging
- Use socialseed_tasker.observability.logging.get_logger(name) to obtain a structured logger.
- Logs are JSON objects with keys: timestamp, level, logger, message, trace_id (optional), plus any extra fields.

Metrics
- Use socialseed_tasker.observability.metrics.observe_operation(component, operation) as a context manager to instrument operations.
- Metrics available:
  - tasker_requests_total{component,operation,result}
  - tasker_request_duration_seconds{component,operation}
  - tasker_inprogress_requests{component,operation}

Prometheus exporter
- Enable exporter by setting TASKER_METRICS_ENABLED=1 in environment or by calling socialseed_tasker.observability.exporter.start_exporter(port).
- Scrape endpoint: http://<host>:<TASKER_METRICS_PORT>/metrics

Examples
- In code:
  from socialseed_tasker.observability.logging import get_logger
  from socialseed_tasker.observability.metrics import observe_operation

  logger = get_logger("tasker.example")
  with observe_operation("example", "do_work"):
      logger.info("starting work", extra={"job_id": "123"})
