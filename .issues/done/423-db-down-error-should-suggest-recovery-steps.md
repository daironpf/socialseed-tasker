# Issue #423: DB down error should suggest recovery steps

## Description
When Neo4j is not running and the user runs a CLI command, the error message says "Database connection failed: Check that Neo4j is running and accessible." This is clear but lacks actionable next steps for the user.

Current error:
```
Database connection failed: Check that Neo4j is running and accessible.
```

## Expected Behavior
The error message should include a suggestion for recovery, such as:
```
Database connection failed: Check that Neo4j is running and accessible.

Tip: Start the database with:
  docker compose -f .agent/tasker/docker-compose.yml --profile api start tasker-db
```

## Actual Behavior
The error message only states the problem without suggesting how to fix it.

## Steps to Reproduce
1. Stop the Neo4j container: `docker compose -f .agent/tasker/docker-compose.yml --profile api stop tasker-db`
2. Run any CLI command: `tasker issue list`
3. Observe the error message

## Status: RESOLVED

## Priority: LOW

## Component
CLI

## Suggested Fix
Extend the error handler in the CLI to detect Docker environment and include a suggestion to start Neo4j via `docker compose` or `tasker restart`.

## Impact
Low. The error is clear but not actionable for new users unfamiliar with the Docker setup.

## Related Issues
- (none)

## Changes Made
1. Added `DB_CONNECTION_TIP` constant in `cli/app.py` with Docker compose start command and link to quick-start docs.
2. Appended `console.print(DB_CONNECTION_TIP)` after each of the three "Database connection failed" paths in `handle_error()`:
   - `GraphPortError("Neo4j operation failed in ...")`
   - `RuntimeError("Cannot connect to Neo4j ...")`
   - `RemoteServiceError("DATABASE_CONNECTION_ERROR" or "Connection error")`
3. Updated three tests in `tests/unit/test_cli_commands.py` to assert `"docker compose up -d" in captured.out`.

## Verification
1. Run `tasker issue list` with Neo4j stopped — output includes `Tip: Start the database with: docker compose up -d`.
2. Run `pytest tests/unit/test_cli_commands.py::TestErrorHandling -v` — all 4 tests pass.
