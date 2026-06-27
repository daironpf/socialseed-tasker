# Issue #277: API Endpoints Return 500 in Docker Container

## Description
During the Inventory System test, when Docker was accessible and the API server was running, all endpoints except `/health` returned 500 INTERNAL_ERROR. This includes `/components`, `/issues`, and `/workable-issues`.

## Expected Behavior
API endpoints should return proper JSON responses (200, 400, etc.) based on the request.

## Actual Behavior
All endpoints return: `{"data":null,"error":{"code":"INTERNAL_ERROR","message":"An unexpected error occurred"}}`

## Steps to Reproduce
1. Start services with `docker compose up -d`
2. Wait for containers to be healthy
3. Call any API endpoint: `curl http://localhost:8000/api/v1/components`
4. Observe 500 error response

## Status: COMPLETED

## Resolution Notes
This issue is resolved by the solution in issue #276. The `tasker restart` command provides the mechanism to rebuild Docker images after code changes.

Users should always run `tasker restart` (not just `docker compose up`) after any code changes to ensure the container has the latest version.

The behavior is now documented in:
- `.agent/README.md` - tasker restart command
- `docs/CLI_COMMANDS.md` - Server Management section

## Priority: HIGH

## Component
API / Infrastructure

## Investigation Notes
- `/health` endpoint works correctly
- This may be related to the Docker image having an older version of the code
- The local `pip install -e .` works, but Docker container may not have the latest code
- The fix from issue #274 was applied to source but may not be in the Docker image

## Suggested Fix
1. Ensure Docker image is rebuilt after code changes: `docker compose build --no-cache`
2. Use `tasker restart` command to rebuild and restart containers
3. Add health check for API endpoints in the Docker startup sequence

## Related Issues
- Related to issue #274 (original workable-issues fix)
- Related to issue #276 (Docker rebuild command)