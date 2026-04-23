# Issue #43: Create Pinia stores for state management

## Description

Set up Pinia stores to manage the application state for issues, components, and UI state.

### Requirements

- Create `frontend/src/stores/` directory
- Create `issuesStore.ts`:
  - State: `issues: Issue[]`, `loading: boolean`, `error: string | null`, `pagination: PaginationMeta`
  - Actions: `fetchIssues(filters?)`, `fetchIssue(id)`, `createIssue(data)`, `updateIssue(id, data)`, `deleteIssue(id)`, `closeIssue(id)`, `fetchBlockedIssues()`
  - Getters: `issuesByStatus`, `issuesByPriority`, `issuesByComponent`, `openIssuesCount`, `blockedIssuesCount`

- Create `componentsStore.ts`:
  - State: `components: Component[]`, `loading: boolean`, `error: string | null`
  - Actions: `fetchComponents(project?)`, `fetchComponent(id)`, `createComponent(data)`, `updateComponent(id, data)`, `deleteComponent(id)`
  - Getters: `getComponentById(id)`, `componentsByProject`

- Create `uiStore.ts`:
  - State: `selectedIssueId: string | null`, `sidebarOpen: boolean`, `viewMode: 'board' | 'list'`, `filters: { status, priority, component, search }`, `darkMode: boolean`
  - Actions: `setSelectedIssue(id)`, `toggleSidebar()`, `setViewMode(mode)`, `setFilter(key, value)`, `clearFilters()`, `toggleDarkMode()`
  - Getters: `filteredIssues` (computed from issuesStore with current filters)

### Technical Details

- Use Pinia `defineStore` with Composition API style (`setup` syntax)
- All async actions should handle loading and error states
- Stores should be reactive and work with Vue DevTools
- Implement optimistic updates where appropriate (e.g., close issue)

### Expected File Paths

- `frontend/src/stores/issuesStore.ts`
- `frontend/src/stores/componentsStore.ts`
- `frontend/src/stores/uiStore.ts`

### Business Value

Centralized state management enables reactive UI updates, consistent data flow, and separation of concerns between data fetching and presentation.

## Status: COMPLETED
