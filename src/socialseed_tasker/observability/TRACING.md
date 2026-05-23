OpenTelemetry Tracing and Jaeger

Overview
- Tracing is configured in src/socialseed_tasker/observability/tracing.py.
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
- Unit tests use an in-memory exporter (src/socialseed_tasker/observability/test_exporter.py).
- Integration tests query Jaeger HTTP API; set TASKER_INTEGRATION=1 to enable.

Notes
- Tracing initialization is safe to call multiple times; it is idempotent.
- In production, configure sampling and exporter according to scale and privacy requirements.
