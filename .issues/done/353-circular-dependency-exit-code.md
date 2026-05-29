# Issue #353: CLI returns exit code 0 when circular dependency is detected

## Description
When `tasker dependency add` detects a cycle, it prints a clear error message but returns exit code 0 instead of non-zero. This breaks CI/CD pipelines that rely on exit codes.

## Expected Behavior
Exit code should be 1 (or non-zero) when a circular dependency is rejected.

## Actual Behavior
Exit code is 0 even though the operation failed.

## Steps to Reproduce
1. Create issue A and B
2. Add dependency A -> B
3. Run `tasker dependency add B --depends-on A`
4. Check `$LASTEXITCODE` — it's 0

## Status: PENDING

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
Return exit code 1 when a circular dependency is rejected.

## Impact
CI/CD pipelines cannot detect failed dependency operations by exit code alone.
