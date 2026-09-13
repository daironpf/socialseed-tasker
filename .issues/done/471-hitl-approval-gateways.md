# Issue #471: Implement Human-in-the-Loop (HITL) approval gateways

## Description
Create an authorization interface for when an agent requests to execute critical actions (push to main, DB migrations, file deletion). Requires human approval before execution.

## Expected Behavior
- Badge/banner in `IssueDetailView` when task is in `WAITING_HUMAN_APPROVAL` state
- Action inspection card: show exact command/payload the agent wants to execute
- Action buttons: **Approve** (green), **Reject with feedback** (red + text field), **Modify parameters**
- Integration with `authStore` for re-authentication or admin role check based on action severity
- New issue status `WAITING_HUMAN_APPROVAL`

## Status: COMPLETED

## Priority: HIGH

## Component
Frontend / Issue Detail / HITL

## Changes Made
1. Added `WAITING_HUMAN_APPROVAL` to `IssueStatus` enum in `types/index.ts`
2. Created `HITLApprovalBanner.vue` component with:
   - Alert banner with warning icon and description
   - Action inspection card showing command/payload, severity badge, target
   - Approve button (green) - sets status to IN_PROGRESS
   - Reject button (red) - opens feedback textarea, sets status to BLOCKED
   - Modify button - opens parameter textarea, sets status to IN_PROGRESS
3. Integrated into IssueDetailView header area (shows when status is WAITING_HUMAN_APPROVAL)
4. Added WAITING_HUMAN_APPROVAL option to status select dropdown
5. Added i18n keys for HITL UI (EN/ES)
6. Handler functions append approval/rejection/modification details to issue description

## Verification
- Issue with WAITING_HUMAN_APPROVAL status shows approval banner
- Action details visible in inspection card with severity badge
- Approve sets status to IN_PROGRESS
- Reject appends feedback to description and sets status to BLOCKED
- Modify appends parameters to description and sets status to IN_PROGRESS

## Related Issues
- #472 (SSE/WebSocket streaming)
