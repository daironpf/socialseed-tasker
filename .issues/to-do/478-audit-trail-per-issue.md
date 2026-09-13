# Issue #478: Implement immutable audit trail per issue

## Description
Add an immutable timeline at the bottom of each issue's detail view to track all historical modifications.

## Expected Behavior
- Descending chronological timeline combining human and agent actions
- Record: status changes, priority changes, policy executions, test runs, HITL approvals
- Format: Avatar + User/Agent + Action executed + Relative timestamp (e.g. "*5 minutes ago*")
- Infinite scroll for large histories
- Filter by action type (status, priority, assignment, agent, system)

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Issue Detail / Audit Trail

## Implementation Plan
1. Create `AuditTrail.vue` component with timeline UI
2. Create `AuditEntry.vue` component with avatar, action, timestamp
3. Implement relative timestamp formatting
4. Add infinite scroll for loading more entries
5. Add filter by action type
6. Integrate into IssueDetailView as a new tab or bottom section
7. Add i18n keys for audit actions

## Acceptance Criteria
- [ ] Timeline displayed in descending chronological order
- [ ] Shows human and agent actions
- [ ] Format: Avatar + User + Action + Relative time
- [ ] Infinite scroll for large histories
- [ ] Filter by action type
- [ ] Immutable (no edit/delete of entries)
- [ ] i18n support

## Verification
- Issue with history shows timeline
- Status changes logged correctly
- Agent actions logged with robot avatar
- Relative timestamps update over time
- Filter narrows displayed entries

## Related Issues
- #477 (Presence indicators)
