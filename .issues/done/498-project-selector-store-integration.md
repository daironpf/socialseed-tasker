# Issue #498: Integrate ProjectSelector with Global Stores

## Description
The `ProjectSelector` in `AppHeader.vue` saves the selected project to localStorage, but `ListView`, `KanbanView`, and `GraphView` render all global data without filtering by the active project. Views must reactively filter issues by the selected project.

## Status: DONE

## Priority: HIGH

## Component
Frontend / Stores / Project Filtering

## Implementation
1. Added `project_id: string` field to `Issue` interface in `types/index.ts`
2. Added `project_id` to `IssueCreateRequest` and `IssueUpdateRequest` types
3. Added `project_id` to all 100 mock issues in `issues.json` (70 socialseed-tasker, 15 auth-service, 15 api-gateway)
4. Added `project` query parameter to `GET /mock/issues` endpoint in `mock-api/server.py`
5. Added `project_id` to `IssueCreate` and `IssueUpdate` models in mock-api
6. Updated `mockApi.ts` to pass `project` filter to the API
7. Added `filteredIssues` computed getter in `issuesStore.ts` that filters by `uiStore.currentProject`
8. Updated `ListView.vue` to use `filteredIssues` for table data and counts
9. Updated `KanbanView.vue` to use `filteredIssues` for columns and counts
10. Updated `GraphView.vue` to use `filteredIssues` for graph nodes and click handlers
11. Added empty state UI in `ListView.vue` and `KanbanView.vue` for projects with no issues
12. Added i18n keys for empty state messages in EN and ES

## Acceptance Criteria
- [x] Each mock issue includes a `project_id` field
- [x] `issuesStore` exposes a `filteredIssues` computed that reacts to project changes
- [x] Changing project in AppHeader instantly updates ListView, Kanban, and Graph
- [x] Empty state shown when selected project has zero issues
- [x] No page reload required for project switch
- [x] i18n support for empty state message

## Verification
- Select "SocialSeed Tasker" in ProjectSelector -> 70 issues shown
- Switch to "Auth Service" -> 15 issues shown, list updates immediately
- Switch to "API Gateway" -> 15 issues shown
- Kanban columns reflect the filtered issues for the active project
- Graph nodes reflect the filtered issues for the active project

## Files Modified
- `frontend/src/types/index.ts` — added `project_id` to Issue, IssueCreateRequest, IssueUpdateRequest
- `frontend/src/stores/issuesStore.ts` — added `filteredIssues` computed
- `frontend/src/views/ListView.vue` — use `filteredIssues`, added empty state
- `frontend/src/views/KanbanView.vue` — use `filteredIssues`, added empty state
- `frontend/src/views/GraphView.vue` — use `filteredIssues` for graph data and click handlers
- `frontend/src/api/mockApi.ts` — pass `project` filter to API
- `frontend/src/locales/en.json` — added `noProjectIssues`, `noProjectIssuesHint`
- `frontend/src/locales/es.json` — added `noProjectIssues`, `noProjectIssuesHint`
- `frontend/dataset-de-pruebas/issues.json` — added `project_id` to all 100 issues
- `mock-api/server.py` — added `project` filter to GET /mock/issues, added `project_id` to models

## Related Issues
- #479 (Organization Project Selector), #428 (Fix Mock Persistence)
