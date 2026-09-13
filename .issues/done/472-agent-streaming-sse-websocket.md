# Issue #472: Implement SSE/WebSocket streaming for live agent reasoning

## Description
Replace the current polling mechanism in the AI Reasoning tab with a real-time EventSource (SSE) or WebSocket connection to observe agent thought flow as it operates.

## Expected Behavior
- Replace polling with SSE/WebSocket connection for live log streaming
- Auto-scroll that can be toggled to follow agent logs as they generate
- Visual distinction between event types: *Thinking*, *Tool Call* (e.g. `read_file`), *Execution Output*, *Error*
- Emergency stop button (**Kill Switch / Cancel Agent Execution**)
- Connection status indicator (connected/disconnected/reconnecting)

## Status: COMPLETED

## Priority: HIGH

## Component
Frontend / Issue Detail / Agent Streaming

## Changes Made
1. Created `useAgentStream.ts` composable for SSE connection management
2. Exponential backoff reconnection (max 5 attempts, base 1s delay)
3. Created `AgentLogStream.vue` component with:
   - Typed event rendering: Thinking (cyan), Progress (green), Files (blue), Debt (amber)
   - Auto-scroll toggle with scroll-to-bottom button
   - Kill Switch button with confirmation dialog
   - Connection status indicator (green=connected, yellow=connecting, red=disconnected)
   - Entry count display
4. Replaced AI Reasoning tab content with AgentLogStream component
5. Auto-connects stream when issue has `agent_working` flag
6. Kill Switch disconnects stream and appends cancellation log
7. Added i18n keys for stream UI (EN/ES)

## Verification
- AI Reasoning tab shows AgentLogStream component
- Connection status indicator shows current state
- Auto-scroll follows new entries when enabled
- Kill Switch cancels stream and shows cancellation message
- Reconnection attempted on disconnect with backoff

## Related Issues
- #471 (HITL approval)
