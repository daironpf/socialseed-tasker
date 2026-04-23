# Issue #47: Build Issue Detail panel with full CRUD operations

## Description

Create a detailed view/panel for a single issue that shows all information and allows editing, closing, deleting, and managing dependencies.

### Requirements

- Create `frontend/src/views/IssueDetailView.vue` (or slide-over panel component)
- Display all issue fields:
  - Title (editable inline)
  - Description (editable, Markdown-supported)
  - Status dropdown (OPEN, IN_PROGRESS, BLOCKED, CLOSED)
  - Priority dropdown (LOW, MEDIUM, HIGH, CRITICAL)
  - Component selector
  - Labels (add/remove tags)
  - Architectural constraints (list)
  - Created/Updated timestamps
- Action buttons: Save, Close Issue, Delete (with confirmation)
- Dependencies section:
  - "Depends on" list with links to each dependency issue
  - "Blocks" list (issues blocked by this one)
  - "Affects" list
  - Add dependency button (search + select from existing issues)
  - Remove dependency button (with confirmation)
  - Visual indicator if adding a dependency would create a cycle
- Dependency chain visualization:
  - Show the full transitive dependency chain as a simple tree or list
- Impact analysis section:
  - Button to run impact analysis
  - Show directly/transitively affected issues
  - Show risk level badge

### Technical Details

- Use a slide-over panel (right side) that can be toggled from board/list views
- All edits go through the issuesStore actions
- Delete requires confirmation modal
- Close issue validates no open dependencies (show error toast if blocked)
- Dependency search uses a debounced input that filters issues by title

### Expected File Paths

- `frontend/src/views/IssueDetailView.vue`
- `frontend/src/components/issue/DependencySection.vue`
- `frontend/src/components/issue/ImpactAnalysisPanel.vue`
- `frontend/src/components/issue/DependencyChainVisual.vue`

### Business Value

The detail view is where all issue management happens - editing, linking dependencies, and understanding impact. It's the core interaction point for users.

## Status: COMPLETED
