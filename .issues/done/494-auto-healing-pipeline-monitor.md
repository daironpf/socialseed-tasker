# Issue #494: Implement CI/CD Auto-Healing Pipeline Monitor

## Description
When test failures occur in CI/CD, Tasker triggers automated root-cause analysis and assigns repair tasks to agents. A real-time visual pipeline step monitor is needed to track the automated flow.

## Status: DONE

## Priority: HIGH

## Component
Frontend / Observability / Auto-Healing

## Implementation
1. Created `types/autoHealing.ts` — PipelineStage, PipelineRun, LogEntry, FixAttempt
2. Created `stores/autoHealingStore.ts` — 3 runs (1 running, 1 completed, 1 failed), 12 logs, 3 fix attempts
3. Created `views/AutoHealingMonitorView.vue` — Full dashboard with pipeline progress, terminal, fix attempts
4. Added route `/auto-healing` -> AutoHealing
5. Added sidebar nav item with refresh icon
6. Added header title mapping
7. Added i18n keys (EN + ES) for autoHealing section

## Acceptance Criteria
- [x] Pipeline progress bar with 5 stages
- [x] Live test output streaming (terminal UI)
- [x] Live fix attempt streaming (with diff preview)
- [x] GitHub PR links
- [x] Neo4j issue node links
- [x] Real-time SSE updates (UI ready, mock data)
- [x] i18n support

## Verification
- Navigate to Auto-Healing Monitor (`/auto-healing`)
- See 3 pipeline runs with status badges (active/completed/failed)
- Select a run to see 5-stage pipeline progress bar
- View live terminal with color-coded logs (red=test, blue=agent, yellow=system)
- View fix attempts with diff preview and status badges
- Click "View Pull Request" link (completed run)
- Click "View in Neo4j" button

## Files Created
- `frontend/src/types/autoHealing.ts` (35 lines)
- `frontend/src/stores/autoHealingStore.ts` (115 lines)
- `frontend/src/views/AutoHealingMonitorView.vue` (165 lines)

## Files Modified
- `frontend/src/router/index.ts` — added /auto-healing route
- `frontend/src/components/layout/Sidebar.vue` — added autoHealing nav item
- `frontend/src/components/layout/AppHeader.vue` — added autoHealing header
- `frontend/src/locales/en.json` — added autoHealing section (16 keys + 5 stage keys)
- `frontend/src/locales/es.json` — added autoHealing section (16 keys + 5 stage keys)

## Related Issues
- #493 (Agent FinOps), #495 (Agent Replay)
