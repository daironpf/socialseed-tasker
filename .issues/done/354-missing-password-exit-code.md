# Issue #354: CLI returns exit code 0 when Neo4j password is missing

## Description
When `TASKER_NEO4J_PASSWORD` is not set and not provided via `-pw`, the CLI shows a helpful error but returns exit code 0.

## Expected Behavior
Exit code should be 1 when required credentials are missing.

## Actual Behavior
Exit code is 0 even though the command cannot execute.

## Steps to Reproduce
1. Unset the TASKER_NEO4J_PASSWORD env var
2. Run `tasker component list`
3. Check `$LASTEXITCODE` — it's 0

## Status: PENDING

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Return exit code 1 when required credentials are missing.

## Impact
Automated scripts cannot detect authentication failures by exit code.
