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

## Status: PENDING

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
[Leave empty]

## Verification
[Leave empty]
