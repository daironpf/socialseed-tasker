# Issue #485: Add policy delete button to PoliciesView

## Description
Connect the existing `deletePolicy()` function in Pinia store to the UI with a delete button on each policy card.

## Expected Behavior
- Delete button (trash icon) on each policy card in `PoliciesView`
- Confirmation modal explaining consequences of deleting the policy on active rules
- Toast notification on successful deletion
- Optimistic UI update (remove card immediately, revert on error)

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Policies / Delete

## Implementation Plan
1. Add delete button (trash icon) to policy card template
2. Create confirmation modal with consequences warning
3. Call `policiesStore.deletePolicy(id)` on confirm
4. Add toast notification on success/error
5. Implement optimistic UI update
6. Add i18n keys for delete confirmation text

## Acceptance Criteria
- [ ] Delete button on each policy card
- [ ] Confirmation modal with consequences warning
- [ ] Successful deletion shows toast
- [ ] Optimistic UI update
- [ ] Error reverts UI change
- [ ] i18n support

## Verification
- Click delete button on policy card
- Confirmation modal appears with warning
- Confirm deletes policy and shows toast
- Policy card removed from view
- Error shows toast and reverts change

## Related Issues
- #486 (Bulk actions in ListView)
