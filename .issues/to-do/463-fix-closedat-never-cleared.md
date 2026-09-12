# Issue #463: closed_at never cleared when reopening issues

## Description
When an issue is changed from CLOSED to any other status, `closed_at` is set to `undefined` in the update body. JavaScript's `JSON.stringify` strips `undefined` keys entirely, so the backend never receives the field, and the stale `closed_at` timestamp persists forever.

This affects three code paths:
- IssueDetailView save: `body.closed_at = undefined` is stripped
- KanbanView drag-drop reopening: no else clause to clear closed_at
- IssueUpdateRequest type: `closed_at` should accept `null`

The `AvgResolutionTime.vue` component uses `closed_at` to compute resolution times. A reopened issue still carrying a stale `closed_at` would incorrectly appear as "resolved" and corrupt the resolution time statistics.

## Status: TODO

## Priority: HIGH

## Component
Frontend / IssueDetailView, KanbanView, types

## Acceptance Criteria
1. Change `undefined` to `null` in IssueDetailView save when reopening
2. Add `closed_at: null` in KanbanView when dragging FROM closed to another status
3. Update `IssueUpdateRequest.closed_at` type to `string | null`
4. `npm run build` passes

## Related Issues
- None
