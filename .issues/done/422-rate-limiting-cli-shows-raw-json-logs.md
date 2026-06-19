# Issue #422: Rate limiting shows raw JSON warning logs instead of user-friendly message

## Description
When the CLI hits the API rate limit, raw JSON warning logs from `httpx` and `api_client` are printed to stderr interleaved with the command output. This pollutes the terminal and confuses users who expect a clean error message.

Example of current output:
```
{"timestamp": "2026-06-09T15:51:38.032039Z", "level": "WARNING", "logger": "socialseed_tasker.infrastructure.http.api_client", "message": "Rate limited (attempt 1/3). Retrying in 1s..."}
```

## Expected Behavior
The CLI should display a clean, formatted message like:
```
[WARNING] Rate limited. Retrying in 1s... (attempt 1/3)
```
Raw JSON should only appear when `--verbose` or `--debug` flags are used.

## Actual Behavior
Raw JSON log lines are printed directly to the terminal, making the output noisy and hard to read.

## Steps to Reproduce
1. Run `tasker issue list` multiple times in rapid succession (or batch operations)
2. Observe the raw JSON warning lines interleaved with the CLI table output

## Status: RESOLVED

## Priority: LOW

## Component
CLI

## Suggested Fix
Add a log formatter in the CLI that intercepts HTTP client logs (httpx, api_client) and formats them as user-friendly messages instead of raw JSON. Use `--verbose`/`--debug` flags to control verbosity.

## Impact
Low. The rate limiting retry mechanism works correctly; this only affects user experience by showing noisy JSON logs.

## Related Issues
- (none)

## Changes Made
1. Added `configure_cli_logging()` in `cli/app.py` — sets up plain-text logging format `[LEVEL] message` instead of JSON. Removes any existing JSON handlers from the root logger.
2. Added `--verbose` flag to the CLI `main()` callback — when set, shows DEBUG-level logs with logger names. By default only INFO+ messages are displayed in compact text format.
3. Changed rate limiting logs in `api_client.py` from `logger.warning` to `logger.info` — retry messages now only appear when `--verbose` is enabled.
4. Suppressed `httpcore` logger at WARNING level to prevent noise from HTTP connection logs.

## Verification
1. Run `tasker issue list` normally — no JSON log lines should appear during rate limiting.
2. Run `tasker --verbose issue list` — rate limiting retry messages appear as `[INFO] Rate limited (attempt 1/3). Retrying in 1s...`.
3. Run `tasker --help` — verify `--verbose` flag appears in options.
4. JSON logging still works in API server mode (uvicorn) via `observability/logging.py`.
