# Issue #427: Fix ListView search and filter functionality

## Description
The ListView component has search, status filter, and priority filter inputs in the UI, but they don't actually filter the list. The `filteredList` computed property simply returns `issuesStore.issues` without applying any of the local filter refs.

## Expected Behavior
- Typing in the search field should filter issues by title, description, or ID
- Selecting a status should filter by OPEN, IN_PROGRESS, BLOCKED, CLOSED
- Selecting a priority should filter by CRITICAL, HIGH, MEDIUM, LOW
- All three filters should work together (AND logic)

## Actual Behavior
The search input, status dropdown, and priority dropdown are present but have no effect on the displayed list.

## Steps to Reproduce
1. Navigate to `/list`
2. Type in the search box — no filtering occurs
3. Select a status from the dropdown — no filtering occurs
4. Select a priority — no filtering occurs

## Status: COMPLETED

## Priority: HIGH

## Component
Frontend / `src/views/ListView.vue`

## Changes Made
1. Updated `filteredList` computed to apply all active filters (search, status, priority, component)
2. Added component filter dropdown to the filter bar
3. Added results count indicator ("Showing X of Y issues")
4. Search now matches against title, ID, and description

## Verification
- Search filters by title, ID, or description in real-time
- Status dropdown filters correctly (OPEN, IN_PROGRESS, BLOCKED, CLOSED)
- Priority dropdown filters correctly (CRITICAL, HIGH, MEDIUM, LOW)
- Component dropdown filters by assigned component
- All filters work together with AND logic
- Results count updates dynamically

## Related Issues
- #428: Fix mock persistence for closeIssue and deleteIssue
