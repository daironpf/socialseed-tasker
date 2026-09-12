# Issue #428: Fix mock persistence for closeIssue and deleteIssue

## Description
In mock mode, `closeIssue()` and `deleteIssue()` in `mockApi.ts` do not persist changes to the JSON files. `closeIssue()` fetches the issue and returns a new object with status CLOSED but never calls the API to save it. `deleteIssue()` has an empty function body — it's a no-op.

## Expected Behavior
- `closeIssue(id)` should call `PATCH /mock/issues/{id}` with `{ status: "CLOSED", closed_at: "..." }` and persist to `issues.json`
- `deleteIssue(id)` should call `DELETE /mock/issues/{id}` and remove from `issues.json`

## Actual Behavior
- `closeIssue()` returned a modified object locally but the change was lost on next page refresh
- `deleteIssue()` did nothing — the issue remained in the data

## Steps to Reproduce
1. Go to `/list` or `/kanban`
2. Close an issue — it appeared closed in the UI
3. Refresh the page — the issue reverted to its previous status
4. Delete an issue — nothing happened

## Status: COMPLETED

## Priority: HIGH

## Component
Frontend / `src/api/mockApi.ts` + Backend / `mock-api/server.py`

## Changes Made
1. Added `DELETE /mock/issues/{issue_id}` endpoint to `mock-api/server.py`
2. Updated `closeIssue()` to call `PATCH /mock/issues/{id}` with status and closed_at
3. Updated `deleteIssue()` to call `DELETE /mock/issues/{id}`

## Verification
- Close an issue → persists after page refresh
- Delete an issue → removed from data permanently
- Count went from 100 to 99 after delete
- Close returns updated status and closed_at timestamp

## Related Issues
- #427: Fix ListView search and filter functionality
