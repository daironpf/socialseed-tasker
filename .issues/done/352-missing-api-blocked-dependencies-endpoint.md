# Issue #352: API `/api/v1/dependencies/blocked` Returns 404 Not Found

## Description
The REST API endpoint `GET /api/v1/dependencies/blocked` returns a 404 Not Found error. The CLI command `tasker dependency blocked` works correctly, but there is no API equivalent for programmatic access.

This finding was discovered during a black-box evaluation (see `real-test/report.md`).

## Expected Behavior
- `GET /api/v1/dependencies/blocked` should return the list of blocked issues (issues with unresolved dependencies)
- Response format should follow the same structure as other API endpoints (`{ "data": ..., "error": null, "meta": ... }`)

## Actual Behavior
```
GET /api/v1/dependencies/blocked
Status: 404
{ "detail": "Not Found" }
```

## Steps to Reproduce
1. Start tasker API (docker compose up)
2. Create issues with dependencies
3. Run `curl.exe http://localhost:8888/api/v1/dependencies/blocked`
4. Observe 404 Not Found

## Status: PENDING

## Priority: MEDIUM

## Component
API

## Suggested Fix
1. Implement the blocked dependencies endpoint in the FastAPI router (likely in `entrypoints/web_api/routes.py`)
2. Reuse the existing `get_blocked_issues` query from the repository layer
3. Document the endpoint in the API surface
4. Add tests

## Impact
API consumers (frontend, integrations) cannot programmatically query blocked dependency chains. Only CLI users can access this data.

## Related Issues
- FIND-004 (report.md)
- #204 (graph-dependencies-empty — related pagination/API issue)
