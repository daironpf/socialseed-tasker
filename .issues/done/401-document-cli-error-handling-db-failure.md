# Issue #401: Document CLI error handling on database failure

## Description

When Neo4j is stopped, the CLI returns a clean, user-friendly error message: `Database connection failed: Check that Neo4j is running and accessible.` No Python stack trace is exposed, and the exit code is 1 (non-zero). This graceful error handling should be preserved and documented.

## Expected Behavior

Friendly error message, no stack traces, exit code != 0.

## Actual Behavior

Works correctly — exit code 1, clean error, no internal IPs exposed.

## Steps to Reproduce
1. Stop Neo4j container
2. Run `tasker issue list`
3. Observe `Database connection failed: Check that Neo4j is running and accessible.`
4. Check `$LASTEXITCODE` — should be 1

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Add regression tests to ensure error messages never expose stack traces or internal connection details.

## Impact
Maintains good UX and security by not exposing implementation details.
