# Issue #424: Rate limiting in CLI causes timeouts during batch operations

## Description
CLI rate limiting (1s delay between requests) causes commands to hang when creating sequential dependencies. Multiple "Rate limited (attempt 1/3). Retrying in 1s..." messages appear during bulk operations, making batch dependency creation extremely slow.

## Expected Behavior
Batch operations (e.g., creating multiple dependencies in sequence) should complete within a reasonable time without excessive rate-limit retries.

## Actual Behavior
When creating 5+ dependencies sequentially, the CLI hits the rate limit frequently, showing up to 6+ retry messages with 1s delays each. This makes batch workflows tedious.

## Steps to Reproduce
1. Run `tasker dependency add <issue-2> --depends-on <issue-1>` for 5+ issues in sequence
2. Observe multiple "Rate limited (attempt 1/3). Retrying in 1s..." messages
3. Commands take much longer than expected

## Status: PENDING

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Increase the burst rate limit or add a batch dependency creation command (e.g., accepting a YAML/JSON file with multiple dependencies).

## Impact
Slows down agent workflows when creating dependency graphs. Affects developer experience during project setup.

## Related Issues
- (none)

## Changes Made

### 1. Increased API rate limiter burst default (20 → 60)
- **File**: `src/socialseed_tasker/infrastructure/web_api/rate_limit.py`
- Changed `BURST` default from 20 to 60, allowing more rapid-fire requests before hitting the rate limit.

### 2. Increased CLI rate limiter burst default (20 → 60)
- **File**: `src/socialseed_tasker/cli/wiring.py`
- Updated all `MemoryRateLimiter` and `RedisRateLimiter` instantiation to use burst=60.

### 3. Improved ApiHttpClient retry with exponential backoff + jitter
- **File**: `src/socialseed_tasker/infrastructure/http/api_client.py`
- Replaced fixed 1s retry delay with exponential backoff: `base_delay * (2^attempt) + jitter`
- Added random jitter (0–0.5s) to prevent thundering herd
- Capped max retry wait at 30s

### 4. Added `add_dependencies_bulk` method to repository interface
- **File**: `src/socialseed_tasker/application/actions.py` (Protocol)
- **File**: `src/socialseed_tasker/infrastructure/api_repository.py` (calls API `POST /issues/{id}/dependencies/bulk`)
- **File**: `src/socialseed_tasker/infrastructure/neo4j_impl/issue_mixin.py` (loops with individual adds + per-item error reporting)

### 5. Added `tasker dependency add-batch` CLI command
- **File**: `src/socialseed_tasker/cli/commands/dependency_commands.py`
- Supports: `--depends-on` (repeatable), `--deps` (comma-separated), `--file` (JSON file)
- Uses `add_dependencies_bulk()` when available (avoids rate-limit retries in API mode)
- Falls back to sequential `add_dependency_action` for direct Neo4j mode
- Reports per-item success/failure

### 6. Updated CLI help text
- **File**: `src/socialseed_tasker/cli/app.py` — Epilog mentions `add-batch` and removed rate-limit warning
- **File**: `src/socialseed_tasker/cli/commands/issue_commands.py` — Points to `dependency add-batch` for bulk operations

## Verification
- [x] Unit tests pass: `pytest tests/unit/ -v`
- [x] API rate limit burst increased and configurable via env `TASKER_RATE_BURST`
- [x] CLI retry uses exponential backoff with jitter
- [x] `tasker dependency add-batch --help` displays correct usage
- [x] Batch command resolves all issue IDs before creating dependencies
- [x] Per-item error reporting shows individual success/failure for each dependency
