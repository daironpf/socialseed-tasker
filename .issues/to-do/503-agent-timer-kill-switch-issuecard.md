# Issue #503: Agent Execution Timer and Kill Switch in IssueCard

## Description
Kanban cards with `agent_working: true` show a pulsing indicator but no execution time or stop control. A live timer showing elapsed time and a kill switch button must be added to `IssueCard.vue`.

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Kanban / IssueCard

## Implementation
1. Add `agent_working_started_at: string | null` field to mock issue data in `mockApi.ts` for issues with `agent_working: true`
2. In `IssueCard.vue`:
   - Calculate elapsed time from `agent_working_started_at` using a reactive `setInterval`
   - Render live timer text: "Working for 12m 45s" (updates every second)
   - Add kill switch button (stop icon) visible on hover or always when agent_working
   - On kill button click: set `agent_working = false`, `agent_working_started_at = null`, show success Toast
3. Use `useToast()` composable for kill confirmation notification
4. Add i18n keys for timer and kill switch

## Acceptance Criteria
- [ ] Live timer updates every second on agent_working cards
- [ ] Timer shows format "Xh Ym Zs" or "Ym Zs" appropriately
- [ ] Kill switch button visible on hover (or always when agent_working)
- [ ] Kill button sets agent_working to false
- [ ] Kill button shows success Toast notification
- [ ] Timer stops after agent is killed
- [ ] i18n support (EN + ES)

## Verification
- View Kanban with agent_working issues -> see live timer counting up
- Hover over card -> kill switch button appears
- Click kill switch -> agent_working becomes false, card loses pulsing indicator
- Toast notification confirms "Agent stopped"
- Timer stops updating after kill

## Files to Create
- (none)

## Files to Modify
- `frontend/src/components/board/IssueCard.vue` — add timer + kill switch
- `frontend/src/api/mockApi.ts` — add agent_working_started_at to mock issues
- `frontend/src/types/index.ts` — add agent_working_started_at to Issue interface
- `frontend/src/locales/en.json` — add agent timer keys
- `frontend/src/locales/es.json` — add agent timer keys

## Related Issues
- #472 (Agent Streaming SSE), #474 (Agent Lifecycle Management)
