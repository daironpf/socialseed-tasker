# Issue #471: Implement Human-in-the-Loop (HITL) approval gateways

## Description
Create an authorization interface for when an agent requests to execute critical actions (push to main, DB migrations, file deletion). Requires human approval before execution.

## Expected Behavior
- Badge/banner in `IssueDetailView` when task is in `WAITING_HUMAN_APPROVAL` state
- Action inspection card: show exact command/payload the agent wants to execute
- Action buttons: **Approve** (green), **Reject with feedback** (red + text field), **Modify parameters**
- Integration with `authStore` for re-authentication or admin role check based on action severity
- New issue status `WAITING_HUMAN_APPROVAL`

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Issue Detail / HITL

## Implementation Plan
1. Add `WAITING_HUMAN_APPROVAL` to `IssueStatus` enum
2. Create `HITLApprovalBanner.vue` component
3. Create `ActionInspectionCard.vue` component showing command/payload
4. Implement approve/reject/modify action buttons
5. Add re-authentication check via `authStore`
6. Integrate into IssueDetailView header area
7. Add i18n keys for HITL UI strings

## Acceptance Criteria
- [ ] `WAITING_HUMAN_APPROVAL` status added to IssueStatus enum
- [ ] Banner displays when issue is in waiting state
- [ ] Action inspection card shows command/payload details
- [ ] Approve button (green) triggers execution
- [ ] Reject button (red) with feedback text field
- [ ] Modify parameters option available
- [ ] Re-authentication required for critical actions
- [ ] i18n support

## Verification
- Issue with `WAITING_HUMAN_APPROVAL` status shows approval banner
- Action details are visible in inspection card
- Approve sends approval to API
- Reject sends rejection with feedback
- Critical actions require re-authentication

## Related Issues
- #472 (SSE/WebSocket streaming)
