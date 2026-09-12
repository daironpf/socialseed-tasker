# Issue #428: Fix mock persistence for closeIssue and deleteIssue

## Description
In mock mode, `closeIssue()` and `deleteIssue()` in `mockApi.ts` do not persist changes to the JSON files. `closeIssue()` fetches the issue and returns a new object with status CLOSED but never calls the API to save it. `deleteIssue()` has an empty function body — it's a no-op.

## Expected Behavior
- `closeIssue(id)` should call `PATCH /mock/issues/{id}` with `{ status: "CLOSED", closed_at: "..." }` and persist to `issues.json`
- `deleteIssue(id)` should call `DELETE /mock/issues/{id}` (or PATCH with a deleted flag) and remove from `issues.json`

## Actual Behavior
- `closeIssue()` returns a modified object locally but the change is lost on next page refresh
- `deleteIssue()` does nothing — the issue remains in the data

## Steps to Reproduce
1. Go to `/list` or `/kanban`
2. Close an issue — it appears closed in the UI
3. Refresh the page — the issue reverts to its previous status
4. Delete an issue — nothing happens

## Status: OPEN

## Priority: HIGH

## Component
Frontend / `src/api/mockApi.ts` + Backend / `mock-api/server.py`

## Suggested Fix
1. Add a `DELETE /mock/issues/{id}` endpoint to `server.py`
2. Update `closeIssue()` in `mockApi.ts` to call `PATCH /mock/issues/{id}`
3. Update `deleteIssue()` in `mockApi.ts` to call `DELETE /mock/issues/{id}`

## Impact
Data integrity issue — users think they've made changes but nothing persists.

## Related Issues
- #427: Fix ListView search and filter functionality
