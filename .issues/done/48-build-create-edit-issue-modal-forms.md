# Issue #48: Build Create/Edit Issue modal forms

## Description

Create modal-based forms for creating new issues and editing existing ones.

### Requirements

- Create `frontend/src/components/issue/CreateIssueModal.vue`:
  - Fields: Title (required), Description, Priority (dropdown, default MEDIUM), Component (dropdown, required), Labels (tag input), Architectural Constraints (tag input)
  - Validation: Title required, Component required
  - Submit button calls `createIssue` from issuesStore
  - On success: close modal, show success toast, refresh issues list
  - On error: show error message in modal

- Create `frontend/src/components/issue/EditIssueModal.vue`:
  - Same fields as CreateIssueModal, pre-populated with existing values
  - Submit button calls `updateIssue` from issuesStore
  - On success: close modal, show success toast, refresh issues list
  - On error: show error message in modal

- Both modals should:
  - Be accessible (focus trap, ESC to close, ARIA labels)
  - Have a loading state during submission
  - Support keyboard navigation

### Technical Details

- Use the Modal.vue component from Issue #44 as the base
- Form validation with simple reactive validation (no external library needed)
- Component dropdown populated from componentsStore
- Label input: type and press Enter to add, click X to remove

### Expected File Paths

- `frontend/src/components/issue/CreateIssueModal.vue`
- `frontend/src/components/issue/EditIssueModal.vue`

### Business Value

Users need intuitive forms to create and edit issues quickly. Modal forms keep context without navigating away from the current view.

## Status: COMPLETED
