# Issue #501: Governance Validation Modal for Issue Closure

## Description
Per governance rules, an issue cannot be CLOSED unless it contains a solution summary and affected files. A `GovernanceValidationModal` must intercept closure attempts and block them when requirements are unmet, showing which policies are violated.

## Status: TODO

## Priority: HIGH

## Component
Frontend / Issue Detail / Governance

## Implementation
1. Add `governance` object to mock issue data in `mockApi.ts`:
   ```json
   "governance": {
     "has_solution_summary": false,
     "has_file_impact": false,
     "policy_violations": ["Missing Solution Summary", "No affected files linked"]
   }
   ```
2. Add `GovernanceValidation` type to Issue interface in `types/index.ts`
3. Create `GovernanceValidationModal.vue` component:
   - Warning modal with issue title
   - List of missing requirements (solution summary, affected files)
   - List of violated policies
   - "Fix Issues" button (closes modal) and "Override" button (forces closure, admin only)
4. In `KanbanView.vue`: intercept drop to CLOSED column, check governance, revert if unmet
5. In `IssueDetailView.vue`: intercept status change to CLOSED, check governance, block if unmet
6. Add i18n keys for governance section

## Acceptance Criteria
- [ ] Governance data present in mock issues
- [ ] `GovernanceValidationModal` component created
- [ ] Modal lists all missing requirements with icons
- [ ] Modal shows violated policies
- [ ] Drag to CLOSED in Kanban blocked when governance fails
- [ ] Status change to CLOSED in Detail blocked when governance fails
- [ ] "Override" option available for admin users
- [ ] i18n support (EN + ES)

## Verification
- Open IssueDetailView for issue without solution summary
- Try to change status to CLOSED -> modal appears listing violations
- Close modal -> status reverts to previous
- Drag issue to CLOSED column in Kanban -> same modal appears
- Click "Override" -> issue closes despite violations
- Issue with both requirements met -> closes normally

## Files to Create
- `frontend/src/components/issue/GovernanceValidationModal.vue`

## Files to Modify
- `frontend/src/types/index.ts` — add GovernanceValidation interface
- `frontend/src/api/mockApi.ts` — add governance to mock issues
- `frontend/src/views/KanbanView.vue` — intercept CLOSED drop
- `frontend/src/views/IssueDetailView.vue` — intercept CLOSED status change
- `frontend/src/locales/en.json` — add governance keys
- `frontend/src/locales/es.json` — add governance keys

## Related Issues
- #82 (Active Policy Enforcement), #84 (Graph Policy Engine)
