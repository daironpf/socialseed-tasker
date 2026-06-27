# Issue #276: Docker Image Not Rebuilt After Code Fix

## Description
The fix from issue #274 (workable-issues endpoint 500 error) was applied to the source code but not deployed to the Docker container. When testing with `docker-compose up`, the API still returns 500 error because it uses an older build without the fix.

## Expected Behavior
After fixing a bug in the source code, running `docker compose up` should use the updated code.

## Actual Behavior
The docker-compose.yml builds tasker-api from local source, but when the container is started, it uses the old build. The fix is not applied until explicitly rebuilding with `docker compose build`.

## Steps to Reproduce
1. Make a code fix
2. Run `docker compose up -d`
3. The container still has the old code

## Status: COMPLETED

## Priority: HIGH

## Component
Infrastructure/Docker

## Suggested Fix
Either:
1. Add a note in the workflow documentation to always rebuild after code changes
2. Add a rebuild step in docker-compose.yml to always pull latest source
3. Add a `tasker deploy` or `tasker restart` command that rebuilds and restarts containers

## Impact
Developers may think a bug is still present when it's actually just a deployment issue.

## Related Issues
- Related to issue #274 (original bug fix)