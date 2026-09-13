# Issue #477: Real-time user and agent presence indicators

## Description
Show real-time activity indicators for which team members or agents are currently inspecting or modifying UI elements.

## Expected Behavior
- Floating avatars in `IssueDetailView` header showing who has the issue open
- Live typing indicator ("*Agent [Arch-Bot] is generating a solution...*")
- Optimistic locking or visual warning when two users/agents edit the same field simultaneously
- Presence heartbeat every 30 seconds
- Auto-expire presence after 60 seconds of inactivity

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Real-time / Presence

## Implementation Plan
1. Create `usePresence` composable for presence state management
2. Implement presence heartbeat via API calls
3. Create `PresenceAvatars.vue` component for issue header
4. Add typing indicator component
5. Implement field-level conflict detection
6. Integrate into IssueDetailView and ListView

## Acceptance Criteria
- [ ] Floating avatars show who has issue open
- [ ] Typing indicator for active agent work
- [ ] Visual warning on field conflicts
- [ ] Presence heartbeat every 30s
- [ ] Auto-expire after 60s inactivity
- [ ] i18n support

## Verification
- Open same issue in two tabs - both show presence avatars
- Agent working shows typing indicator
- Editing same field shows conflict warning
- Presence disappears after 60s inactivity

## Related Issues
- #478 (Audit trail)
