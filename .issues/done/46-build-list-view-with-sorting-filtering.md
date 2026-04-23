# Issue #46: Build the List view with sorting and filtering

## Description

Create an alternative List view that displays issues in a sortable, filterable table format.

### Requirements

- Create `frontend/src/views/ListView.vue`
- Table columns: Title, Status, Priority, Component, Labels, Created, Actions
- Sortable columns (click header to sort): Title, Priority, Created
- Filter bar at top with:
  - Search input (filters by title and description)
  - Status multi-select dropdown
  - Priority multi-select dropdown
  - Component dropdown
  - Clear all filters button
- Each row has action buttons: View, Edit, Close, Delete
- Pagination controls at bottom (page size selector: 10, 25, 50)
- Blocked issues highlighted with a red left border
- Critical priority issues highlighted with an orange left border
- Responsive: on mobile, cards instead of table

### Technical Details

- Use the `filteredIssues` getter from uiStore
- Sorting done client-side for simplicity
- Pagination uses the backend's pagination when available
- Table should be accessible with proper `scope` attributes

### Expected File Paths

- `frontend/src/views/ListView.vue`
- `frontend/src/components/list/IssueTableRow.vue`
- `frontend/src/components/list/FilterBar.vue`

### Business Value

The list view is ideal for users who prefer a dense, spreadsheet-like overview and need to quickly scan and sort through many issues.

## Status: COMPLETED
