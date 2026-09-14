# Issue #484: Add assignee and creator fields to issue forms

## Description
Add the missing `assignee` and `created_by` fields to the issue creation and editing lifecycle.

## Expected Behavior
- Assignee dropdown in `CreateIssueModal` and `IssueDetailView` (including both humans and agents)
- Auto-capture authenticated user as `created_by` when creating an issue
- Quick re-assignment from Kanban card or List row
- Avatar display for assignee and creator in issue detail
- Empty state for unassigned issues

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Issue / Assignment

## Implementation Plan
1. Add `assignee` dropdown to `CreateIssueModal.vue`
2. Add `assignee` display/edit to `IssueDetailView.vue`
3. Auto-set `created_by` from `authStore` on issue creation
4. Add quick-assign action to IssueCard and list rows
5. Display assignee/creator avatars in detail view
6. Add i18n keys for assignment labels

## Acceptance Criteria
- [ ] Assignee dropdown in CreateIssueModal with all users
- [ ] Assignee display/edit in IssueDetailView
- [ ] Auto-capture created_by from authenticated user
- [ ] Quick-assign from Kanban/List
- [ ] Avatar display for assignee/creator
- [ ] Empty state for unassigned
- [ ] i18n support

## Verification
- Create issue with assignee selected
- Issue detail shows assignee avatar and name
- created_by auto-set to current user
- Quick-assign changes assignee from kanban card
- Unassigned shows empty state

## Related Issues
- #485 (Policy delete button)
