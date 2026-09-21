# Issue #498: Integrate ProjectSelector with Global Stores

## Description
The `ProjectSelector` in `AppHeader.vue` saves the selected project to localStorage, but `ListView`, `KanbanView`, and `GraphView` render all global data without filtering by the active project. Views must reactively filter issues by the selected project.

## Status: TODO

## Priority: HIGH

## Component
Frontend / Stores / Project Filtering

## Implementation
1. Add `project_id: string` field to every issue in `mockApi.ts` mock data
2. Add computed `filteredIssues` getter in `issuesStore.ts` that filters by `uiStore.selectedProject`
3. Update `ListView.vue` to use `filteredIssues` instead of raw `issues`
4. Update `KanbanView.vue` to use `filteredIssues` instead of raw `issues`
5. Update `GraphView.vue` to use `filteredIssues` for node rendering
6. Add empty state UI when selected project has no associated issues

## Acceptance Criteria
- [ ] Each mock issue includes a `project_id` field
- [ ] `issuesStore` exposes a `filteredIssues` computed that reacts to project changes
- [ ] Changing project in AppHeader instantly updates ListView, Kanban, and Graph
- [ ] Empty state shown when selected project has zero issues
- [ ] No page reload required for project switch
- [ ] i18n support for empty state message

## Verification
- Select "SocialSeed Core" in ProjectSelector -> only SocialSeed issues shown
- Switch to "Agent Toolkit" -> list updates immediately
- Select a project with no issues -> see friendly empty state
- Kanban columns reflect the filtered issues for the active project
- Graph nodes reflect the filtered issues for the active project

## Files to Create
- (none)

## Files to Modify
- `frontend/src/stores/issuesStore.ts` — add `filteredIssues` computed
- `frontend/src/stores/uiStore.ts` — ensure `selectedProject` is reactive
- `frontend/src/views/ListView.vue` — use `filteredIssues`
- `frontend/src/views/KanbanView.vue` — use `filteredIssues`
- `frontend/src/views/GraphView.vue` — use `filteredIssues`
- `frontend/src/api/mockApi.ts` — add `project_id` to mock issues
- `frontend/src/types/index.ts` — add `project_id` to Issue interface
- `frontend/src/locales/en.json` — add empty state keys
- `frontend/src/locales/es.json` — add empty state keys

## Related Issues
- #479 (Organization Project Selector), #428 (Fix Mock Persistence)
