# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project adheres to Semantic Versioning.

## [Unreleased]

## [v1.0.2] - 2026-06-30

### Added
- Full Stack mode (option 3) in `tasker init`: starts Neo4j + FastAPI + Kanban Board
- Frontend pre-build step in `tasker init --full` before scaffolding
- Board Dockerfile + nginx.conf copied during scaffold for containerised deployment
- Docker daemon pre-check in init command before `docker compose up`

### Changed
- Frontend Dockerfile: single-stage nginx serving pre-built static files (no npm in build)
- Root docker-compose.yml: added tasker-board service
- Init command compose profile: now supports `direct`, `api`, and `full` modes
- Scaffolder `_copy_frontend_build()`: also copies Dockerfile and nginx.conf

### Fixed
- Board Dockerfile healthcheck: use `127.0.0.1` instead of `localhost` (DNS resolution)
- Frontend Dockerfile COPY paths relative to build context

## [v1.0.1] - 2026-05-23

### Added
- [#312] Chaos Testing Harness: `tools/chaos/`, `chaosctl.py`, 3 scenarios (redis-flap, api-latency, worker-cpu-spike), unit & integration tests
- [#313] Data Export and Backup System: `src/socialseed_tasker/backup/`, CLI backup commands, scheduled backups via docker-compose
- [#314] Multi-Tenant Support: `src/socialseed_tasker/tenancy/`, `TenantContext`, `TenantMiddleware`, `NamespacedStorage`, tenant CLI & API
- [#315] Distributed Tracing with OpenTelemetry and Jaeger: `src/socialseed_tasker/observability/tracing.py`, FastAPI/Celery/Requests instrumentation, Jaeger exporter
- [#316] Feature Flags and Runtime Configuration: `src/socialseed_tasker/config/`, `FeatureFlagStore`, `FeatureFlagClient`, `RuntimeConfig` with dynamic polling reload, admin API and CLI
- [#317] Data Retention Policy Engine and GDPR Compliance: `src/socialseed_tasker/privacy/`, `evaluate_policy`, `RetentionWorker`, subject export/delete handlers, audit log
- Pre-existing regressions fixed: `_group_actions` → `list(sub.choices.items())` for Python 3.14 argparse compat; `datetime.utcnow()` → `datetime.now(datetime.timezone.utc)`; `yaml.safe_load(path)` → `yaml.safe_load(open(path))`

### Changed
- `wiring.py` Container extended with `runtime_config`, `privacy_handlers` fields
- `tracing.py` Jaeger/FastAPI/Celery instrumentations made lazy (lazy import to avoid hard dependencies)

## [v1.0.0] - 2026-05-21

### Added
- Initial public release with core features: modular architecture, Neo4j adapter, parser adapter, CLI, repositories, use cases, tests, CI, and examples.

### Changed
- N/A

### Fixed
- N/A
