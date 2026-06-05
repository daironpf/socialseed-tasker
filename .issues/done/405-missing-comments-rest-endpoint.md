# Issue #405: Missing REST endpoint for issue comments

## Description
Issue comments exist only through GitHub mirroring (`github_mirror.py`). There is no standalone REST endpoint at `/api/v1/issues/{id}/comments` for creating or reading comments directly via the Tasker API.

## Expected Behavior
A REST endpoint `POST /api/v1/issues/{id}/comments` should exist to allow adding comments to any issue, and `GET /api/v1/issues/{id}/comments` to retrieve them.

## Actual Behavior
`POST /api/v1/issues/ID/comments` returns HTTP 404.

## Steps to Reproduce
1. `curl -X POST http://localhost:8888/api/v1/issues/<any-id>/comments -H "Content-Type: application/json" -d '{"text":"test"}'`
2. Observe 404 response

## Status: PENDING

## Priority: LOW

## Component
API / Issues

## Suggested Fix
Add comment storage (e.g., a `Comment` node or embedded list on the `Issue` node) and expose CRUD routes in `routers/issues.py`.

## Impact
- Audit trail limited to GitHub-linked issues
- No way to annotate issues from the CLI or API
- Reduces value for standalone (non-GitHub) projects
