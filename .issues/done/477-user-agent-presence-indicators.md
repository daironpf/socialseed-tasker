# Issue #477: Real-time user and agent presence indicators

## Description
Show real-time activity indicators for which team members or agents are currently inspecting or modifying UI elements.

## Expected Behavior
- Floating avatars in `IssueDetailView` header showing who has the issue open
- Live typing indicator ("*Agent [Arch-Bot] is generating a solution...*")
- Optimistic locking or visual warning when two users/agents edit the same field simultaneously
- Presence heartbeat every 30 seconds
- Auto-expire presence after 60 seconds of inactivity

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Real-time / Presence

## Changes Made
1. Created `usePresence.ts` composable:
   - Presence state management with Map<issueId, PresenceUser[]>
   - 30s heartbeat interval
   - 60s auto-expire for stale presence
   - `joinPresence()`, `leavePresence()`, `updateField()` methods
   - `viewers`, `typingAgents`, `hasConflict` computed properties
   - Mock presence data generation for demo
   - Local presence ID tracking
2. Created `PresenceAvatars.vue`:
   - Floating avatar stack with overlap (-space-x-2)
   - Green online indicator dot
   - Hover tooltip with username, field being edited, time ago
   - Singular/plural text ("X is viewing" / "X are viewing")
3. Created `TypingIndicator.vue`:
   - Animated bouncing dots (3 dots with staggered delay)
   - Shows agent avatar and name with typing message
   - Purple color scheme for agent distinction
   - Transition enter/exit animations
4. Created `ConflictWarning.vue`:
   - Amber warning banner when same field being edited
   - Warning icon with descriptive text
   - Transition animations
5. Integrated into IssueDetailView:
   - PresenceAvatars in header next to close button
   - TypingIndicator and ConflictWarning after HITL banner
6. Added i18n keys for presence UI (EN/ES)

## Verification
- Presence avatars show in issue header with online indicator
- Typing indicator shows for active agents
- Conflict warning appears when field conflict detected
- Presence auto-expires after 60s inactivity
- Heartbeat maintains presence every 30s
