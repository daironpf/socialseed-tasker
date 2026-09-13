# Issue #479: Add organization selector and multi-project context

## Description
Allow switching repositories or microservices globally from the top bar (`AppHeader`).

## Expected Behavior
- Dropdown in AppHeader showing current project/repository
- Global reactivity in Pinia: changing project automatically updates issues, components, policies, and constraints stores
- Selected project persisted in localStorage
- Visual indicator of current project context
- Project switch confirmation for unsaved changes

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Layout / Project Context

## Implementation Plan
1. Create `ProjectSelector.vue` dropdown component
2. Add `currentProject` to `uiStore` with localStorage persistence
3. Implement store reactivity on project change
4. Add project switch confirmation dialog
5. Integrate into AppHeader
6. Add i18n keys for project selector

## Acceptance Criteria
- [ ] Project dropdown in AppHeader
- [ ] Current project displayed
- [ ] Switching project updates all stores
- [ ] Selection persisted in localStorage
- [ ] Confirmation for unsaved changes
- [ ] i18n support

## Verification
- Dropdown shows current project
- Switching project refreshes issues/components/policies/constraints
- Selection persists on page reload
- Unsaved changes prompt confirmation

## Related Issues
- None
