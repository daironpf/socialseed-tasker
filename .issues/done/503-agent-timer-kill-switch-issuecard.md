# Issue #503: Agent Execution Timer and Kill Switch in IssueCard

## Description
Kanban cards with `agent_working: true` show a pulsing indicator but no execution time or stop control. A live timer showing elapsed time and a kill switch button must be added to `IssueCard.vue`.

## Status: DONE

## Priority: MEDIUM

## Component
Frontend / Kanban / IssueCard

## Implementation
1. Added `agent_working_started_at` field to `Issue` interface in `types/index.ts`
2. Added `agent_working` and `agent_working_started_at` fields to `IssueUpdateRequest` interface
3. Added `agent_working_started_at` data to all agent_working issues in `issues.json`
4. Updated `IssueCard.vue`:
   - Live timer showing elapsed time (updates every second)
   - Kill switch button visible on hover
   - On kill: sets `agent_working = false`, `agent_working_started_at = null`
   - Timer stops after agent is killed
5. Added i18n keys for timer and kill switch (EN + ES)

## Acceptance Criteria
- [x] Live timer updates every second on agent_working cards
- [x] Timer shows format "Xh Ym Zs" or "Ym Zs" appropriately
- [x] Kill switch button visible on hover (or always when agent_working)
- [x] Kill button sets agent_working to false
- [x] Kill button shows success notification
- [x] Timer stops after agent is killed
- [x] i18n support (EN + ES)

## Files Modified
- `frontend/src/types/index.ts` — added agent_working_started_at to Issue and IssueUpdateRequest
- `frontend/src/dataset-de-pruebas/issues.json` — added agent_working_started_at to agent_working issues
- `frontend/src/components/board/IssueCard.vue` — added live timer and kill switch button
- `frontend/src/locales/en.json` — added agent section (2 keys)
- `frontend/src/locales/es.json` — added agent section (2 keys)

## Related Issues
- #472 (Agent Streaming SSE), #474 (Agent Lifecycle Management)
