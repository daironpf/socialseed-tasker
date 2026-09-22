# Issue #501: Governance Validation Modal for Issue Closure

## Description
Per governance rules, an issue cannot be CLOSED unless it contains a solution summary and affected files. A `GovernanceValidationModal` must intercept closure attempts and block them when requirements are unmet, showing which policies are violated.

## Status: DONE

## Priority: HIGH

## Component
Frontend / Issue Detail / Governance

## Implementation
1. Added `GovernanceValidation` interface to `types/index.ts`
2. Added `governance?` optional field to `Issue` interface
3. Added `governance` data to all 100 mock issues in `issues.json` (alternating valid/invalid)
4. Created `GovernanceValidationModal.vue` with:
   - Warning modal with issue title
   - Checklist of missing requirements (solution summary, affected files)
   - List of violated policies
   - "Fix Issues" button (closes modal) and "Override" button (forces closure)
5. In `KanbanView.vue`: intercept drop to CLOSED column, check governance, show modal if unmet
6. In `IssueDetailView.vue`: intercept status change to CLOSED in `save()`, check governance, show modal if unmet
7. Added i18n keys for governance section (EN + ES)

## Acceptance Criteria
- [x] Governance data present in mock issues
- [x] `GovernanceValidationModal` component created
- [x] Modal lists all missing requirements with icons
- [x] Modal shows violated policies
- [x] Drag to CLOSED in Kanban blocked when governance fails
- [x] Status change to CLOSED in Detail blocked when governance fails
- [x] "Override" option available to force closure despite violations
- [x] i18n support (EN + ES)

## Files Created
- `frontend/src/components/issue/GovernanceValidationModal.vue`

## Files Modified
- `frontend/src/types/index.ts` — added GovernanceValidation interface, extended Issue
- `frontend/src/dataset-de-pruebas/issues.json` — added governance to all 100 issues
- `frontend/src/views/KanbanView.vue` — intercept CLOSED drop with governance check
- `frontend/src/views/IssueDetailView.vue` — intercept CLOSED status change with governance check
- `frontend/src/locales/en.json` — added governance section (7 keys)
- `frontend/src/locales/es.json` — added governance section (7 keys)

## Related Issues
- #82 (Active Policy Enforcement), #84 (Graph Policy Engine)
