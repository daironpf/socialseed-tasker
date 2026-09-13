# Issue #472: Implement SSE/WebSocket streaming for live agent reasoning

## Description
Replace the current polling mechanism in the AI Reasoning tab with a real-time EventSource (SSE) or WebSocket connection to observe agent thought flow as it operates.

## Expected Behavior
- Replace polling with SSE/WebSocket connection for live log streaming
- Auto-scroll that can be toggled to follow agent logs as they generate
- Visual distinction between event types: *Thinking*, *Tool Call* (e.g. `read_file`), *Execution Output*, *Error*
- Emergency stop button (**Kill Switch / Cancel Agent Execution**)
- Connection status indicator (connected/disconnected/reconnecting)

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Issue Detail / Agent Streaming

## Implementation Plan
1. Create `useAgentStream` composable for SSE/WebSocket connection management
2. Implement reconnection logic with exponential backoff
3. Create `AgentLogStream.vue` component with typed event rendering
4. Add auto-scroll toggle and scroll-to-bottom button
5. Implement Kill Switch button with confirmation
6. Add connection status indicator
7. Integrate into IssueDetailView AI Reasoning tab

## Acceptance Criteria
- [ ] SSE/WebSocket connection established for live logs
- [ ] Auto-scroll toggle available
- [ ] Visual distinction: Thinking (blue), Tool Call (purple), Output (gray), Error (red)
- [ ] Kill Switch button with confirmation dialog
- [ ] Connection status indicator (connected/disconnected)
- [ ] Reconnection on disconnect with backoff
- [ ] i18n support

## Verification
- Open an issue with active agent
- AI Reasoning tab shows live streaming logs
- Auto-scroll follows new entries
- Kill Switch cancels agent execution
- Disconnect/reconnect handled gracefully

## Related Issues
- #471 (HITL approval)
