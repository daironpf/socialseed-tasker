# Issue #339: Database connection error shows Python traceback

## Description
When Neo4j is down, the CLI shows a structured error but still prints a full Python traceback before it. The structured error (`DATABASE_CONNECTION_ERROR`) is good, but the traceback is noisy.

## Expected Behavior
CLI should show only a clean error message without the Python traceback.

## Actual Behavior
Traceback is printed alongside the structured error message.

## Steps to Reproduce
1. `docker compose stop tasker-db`
2. Run `tasker issue list`

## Status: PENDING

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Suppress traceback in production mode; show only `[ERROR]: Database connection failed - <message>`

## Impact
Confusing for non-technical users

## Related Issues
-
