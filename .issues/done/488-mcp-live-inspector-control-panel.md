# Issue #488: Implement MCP Live Inspector & Connection Control Panel

## Description
Tasker connects with IDEs and autonomous agents (Cursor, Claude Desktop, Windsurf) via the Model Context Protocol (MCP). We need a control plane UI to observe and manage active MCP connections in real time.

## Expected Behavior
- Real-time matrix displaying connected MCP agents with client name, status, and uptime
- Live metrics showing context consumption (in KB/MB) and Cypher queries executed per minute
- "Revoke/Pause Session" action button that immediately terminates or pauses an active MCP session
- SSE or WebSocket updates for live status changes

## Status: DONE

## Priority: HIGH

## Component
Frontend / MCP / Inspector

## Implementation Plan
1. Create `MCPInspectorView.vue` dedicated UI panel
2. Build real-time matrix table for connected MCP agents
3. Implement live metrics display (context consumption, Cypher query rates)
4. Add "Revoke/Pause Session" action buttons
5. Integrate SSE/WebSocket for live status updates
6. Create MCP-specific types and store
7. Add i18n keys for MCP inspector labels
8. Add navigation route and sidebar entry

## Acceptance Criteria
- [x] Real-time matrix with client name, status, uptime
- [x] Live context consumption metrics (KB/MB)
- [x] Live Cypher query rate display (queries/min)
- [x] Revoke/Pause session buttons
- [x] SSE/WebSocket live updates
- [x] i18n support

## Verification
- Navigate to MCP Inspector view
- See connected MCP agents in matrix
- Metrics update in real-time
- Revoke button terminates session
- Pause button pauses session
- Status changes reflect immediately

## Related Issues
- #489 (HITL Command Center)
