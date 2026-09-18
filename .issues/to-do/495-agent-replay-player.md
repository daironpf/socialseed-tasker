# Issue #495: Develop Time-Travel Session Replay Player for Agent Execution

## Description
Auditing agent reasoning requires reviewing exact steps, tool invocations, and Cypher queries executed chronologically. A video-player style scrubber is needed to step backward and forward through an agent's execution history.

## Expected Behavior
- Scrubbable timeline with Play, Pause, Fast-Forward, and Step-By-Step controls
- Synchronized view showing tool calls, files read/edited, and Cypher queries at each second
- Event markers indicating errors, policy violations, or decision branch points

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Observability / Agent Replay

## Implementation Plan
1. Create `AgentReplay.vue` component
2. Build video-player style scrubber timeline
3. Implement Play/Pause/Fast-Forward/Step controls
4. Add synchronized view for tool calls, files, Cypher queries
5. Add event markers for errors, violations, branches
6. Integrate with `GET /issues/{id}/agent-trace` endpoint
7. Add i18n keys for replay controls
8. Add navigation in Observability section

## Acceptance Criteria
- [ ] Scrubbable timeline
- [ ] Play/Pause/Fast-Forward controls
- [ ] Step-By-Step mode
- [ ] Synchronized tool calls view
- [ ] Synchronized files read/edited view
- [ ] Synchronized Cypher queries view
- [ ] Event markers (errors, violations, branches)
- [ ] i18n support

## Verification
- Navigate to Agent Replay for an issue
- See scrubber timeline with events
- Play through agent execution
- Pause at any point
- Step forward/backward
- View tool calls at current position
- View files read/edited at current position
- View Cypher queries at current position
- See event markers on timeline

## Related Issues
- #494 (Auto-Healing Monitor), #496 (PII Guard)
