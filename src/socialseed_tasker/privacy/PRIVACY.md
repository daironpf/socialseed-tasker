# Data Retention & GDPR Compliance

## Overview
Deterministic data retention policy engine, retention worker, and subject export/delete handlers for GDPR compliance.

## Policy Evaluation
- `evaluate_policy(record_meta)` returns `True` (keep) or `False` (eligible for deletion).
- Default retention: issues=3y, comments=2y, logs=90d, storage=1y.
- Override per kind: `TASKER_RETENTION_<KIND>` env var (seconds).
- Per-tenant override: `TASKER_RETENTION_<TENANT>_<KIND>` env var.
- Records tagged `legal-hold` are always kept.

## Retention Worker
- `RetentionWorker` scans `issue_repo` and `storage` for records exceeding policy.
- Archives before deletion if `TASKER_RETENTION_ARCHIVE=1`.
- Writes audit entries to `privacy:audits` in storage.
- Controlled by `TASKER_RETENTION_ENABLED`, `TASKER_RETENTION_INTERVAL`, `TASKER_RETENTION_ARCHIVE_PATH`.

## Subject Export/Delete
- `POST /api/v1/privacy/export` — export all data for `subject_id` as tar.gz.
- `POST /api/v1/privacy/delete` — request deletion (supports `dry_run`).
- `GET /api/v1/privacy/tasks/{task_id}` — task status.
- `GET /api/v1/privacy/audit` — audit log (admin only).

## Environment Variables
| Variable | Default | Description |
|---|---|---|
| `TASKER_RETENTION_ENABLED` | `1` | Enable retention worker |
| `TASKER_RETENTION_INTERVAL` | `3600` | Worker interval in seconds |
| `TASKER_RETENTION_ARCHIVE` | `0` | Archive before deletion |
| `TASKER_RETENTION_ARCHIVE_PATH` | `/tmp/tasker-archives` | Archive output path |
| `TASKER_RETENTION_DRY_RUN` | `0` | Dry-run mode |
| `TASKER_RETENTION_<KIND>` | — | Per-kind retention seconds |
| `TASKER_RETENTION_<TENANT>_<KIND>` | — | Per-tenant per-kind retention seconds |
