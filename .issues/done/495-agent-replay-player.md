# Issue #495: Develop Time-Travel Session Replay Player for Agent Execution

## Description
Auditing agent reasoning requires reviewing exact steps, tool invocations, and Cypher queries executed chronologically. A video-player style scrubber is needed to step backward and forward through an agent's execution history.

## Status: DONE

## Priority: HIGH

## Component
Frontend / Observability / Agent Replay

## Implementation
1. Created `types/agentReplay.ts` — EventType, EventSeverity, ReplayEvent, AgentSession
2. Created `stores/agentReplayStore.ts` — 2 sessions, 14+7 events, play/pause/seek controls
3. Created `views/AgentReplayView.vue` — Full player with scrubber, controls, synchronized views
4. Added route `/replay` -> AgentReplay
5. Added sidebar nav item with play icon
6. Added header title mapping
7. Added i18n keys (EN + ES) for replay section

## Acceptance Criteria
- [x] Scrubbable timeline with event markers
- [x] Play/Pause/Fast-Forward controls (0.5x, 1x, 2x, 4x speeds)
- [x] Step-By-Step mode (forward/backward)
- [x] Synchronized tool calls view
- [x] Synchronized files read/edited view
- [x] Synchronized Cypher queries view
- [x] Event markers (errors=red, violations=amber, decisions=purple, cypher=cyan, tools=blue, files=green)
- [x] i18n support

## Verification
- Navigate to Agent Replay (`/replay`)
- Select a session (ISS-042 or ISS-038)
- See scrubber timeline with colored event markers
- Click play to animate through events
- Pause at any point
- Step forward/backward through events
- View event stream with current event highlighted
- View files affected panel (updates as events appear)
- View Cypher queries panel (queries shown in green terminal style)
- Change playback speed (0.5x to 4x)

## Files Created
- `frontend/src/types/agentReplay.ts` (20 lines)
- `frontend/src/stores/agentReplayStore.ts` (130 lines)
- `frontend/src/views/AgentReplayView.vue` (195 lines)

## Files Modified
- `frontend/src/router/index.ts` — added /replay route
- `frontend/src/components/layout/Sidebar.vue` — added replay nav item
- `frontend/src/components/layout/AppHeader.vue` — added replay header
- `frontend/src/locales/en.json` — added replay section (17 keys)
- `frontend/src/locales/es.json` — added replay section (17 keys)

## Related Issues
- #494 (Auto-Healing Monitor), #496 (PII Guard)
