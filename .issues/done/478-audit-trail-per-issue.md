# Issue #478: Implement immutable audit trail per issue

## Description
Add an immutable timeline at the bottom of each issue's detail view to track all historical modifications.

## Expected Behavior
- Descending chronological timeline combining human and agent actions
- Record: status changes, priority changes, policy executions, test runs, HITL approvals
- Format: Avatar + User/Agent + Action executed + Relative timestamp (e.g. "*5 minutes ago*")
- Infinite scroll for large histories
- Filter by action type (status, priority, assignment, agent, system)

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Issue Detail / Audit Trail

## Changes Made
1. Created `audit.ts` types with `AuditEntry` interface and `AuditAction` type (8 types: status, priority, assignment, agent, system, hitl, comment, label)
2. Created `AuditEntry.vue` component:
   - Timeline layout with vertical line
   - Avatar with color-coded background (human=blue, agent=purple, system=gray)
   - Action type badge with color coding
   - Actor name, description, and details (from→to)
   - Relative timestamp (just now, Xm ago, Xh ago, Xd ago)
3. Created `AuditTrail.vue` component:
   - Filter tabs (All, Status, Priority, Assignment, Agent, System)
   - Sorted by timestamp descending
   - Infinite scroll with "Load more" button (15 entries per page)
   - Empty state with clock icon
4. Integrated into IssueDetailView as "History" tab
5. Mock audit entries (9 entries covering all action types)
6. Added i18n keys for audit UI (EN/ES)

## Verification
- History tab shows audit trail timeline
- Entries sorted by newest first
- Filter tabs narrow by action type
- Load more shows additional entries
- Status changes show from→to values
- Agent actions shown with robot avatar
- Relative timestamps display correctly
