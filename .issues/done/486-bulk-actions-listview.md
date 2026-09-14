# Issue #486: Implement bulk actions in ListView

## Description
Implement multi-row selection for applying batch changes to issues.

## Expected Behavior
- Individual checkbox per row and "Select all" checkbox in table header
- Floating bottom action bar when ≥1 element selected:
  - Batch status change (e.g. Move all to `CLOSED`)
  - Batch assign to agent or human
  - Batch delete with confirmation modal
- Selection count display
- Clear selection button
- Selection persists during filter changes

## Status: PENDING

## Priority: HIGH

## Component
Frontend / ListView / Bulk Actions

## Implementation Plan
1. Add checkbox column to ListView table
2. Add "Select all" checkbox in table header
3. Create `BulkActionsBar.vue` floating bottom bar component
4. Implement batch status change with dropdown
5. Implement batch assign with user dropdown
6. Implement batch delete with confirmation
7. Add selection state to component
8. Add i18n keys for bulk action labels

## Acceptance Criteria
- [ ] Checkbox per row in table
- [ ] Select all checkbox in header
- [ ] Floating action bar when items selected
- [ ] Batch status change option
- [ ] Batch assign option
- [ ] Batch delete with confirmation
- [ ] Selection count displayed
- [ ] Clear selection button
- [ ] i18n support

## Verification
- Select multiple rows via checkboxes
- Action bar appears at bottom
- Batch status change updates all selected
- Batch delete shows confirmation
- Selection count updates correctly
- Clear selection deselects all

## Related Issues
- #487 (Agent creation in CreateUserModal)
