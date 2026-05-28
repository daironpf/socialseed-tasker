# Issue #343: Connection errors dump full Python traceback

## Description
When the API server is unreachable (e.g., Docker not running), the CLI correctly catches the error and shows "Database connection failed: Check that Neo4j is running and accessible." but then proceeds to dump the entire 50+ line Python traceback. The friendly message is buried at the start.

## Expected Behavior
Only the friendly error message should be displayed. The traceback should be suppressed or logged to a file.

## Actual Behavior
After stopping Docker and running `tasker issue list`, the output starts with "Database connection failed: Check that Neo4j is running and accessible." but is immediately followed by a full httpx/typer traceback (50+ lines).

## Steps to Reproduce
1. Stop Docker (docker compose --profile api down)
2. Run `tasker issue list`
3. Observe full traceback after the friendly error message

## Status: COMPLETED

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Catch `RemoteServiceError` / `ConnectError` at the CLI app level and print only the friendly message without traceback. Use `--debug` flag to optionally show tracebacks.

## Impact
Non-developer users will be overwhelmed by the traceback. The exit code is correctly 1.

## Related Issues
- FIND-002 from black-box evaluation 2026-05-28
