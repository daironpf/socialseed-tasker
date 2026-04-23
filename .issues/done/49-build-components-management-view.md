# Issue #49: Build Components management view

## Description

Create a view for managing components (projects/modules) that issues are grouped under.

### Requirements

- Create `frontend/src/views/ComponentsView.vue`
- Display a grid/list of all components showing:
  - Name
  - Description
  - Project
  - Issue count (computed from issuesStore)
  - Created date
- Actions per component:
  - View details (shows all issues for that component)
  - Edit (name, description, project)
  - Delete (with confirmation, force option if has issues)
- "New Component" button opens a modal form
- Create component modal: Name (required), Description, Project (required)
- Edit component modal: same fields, pre-populated

### Technical Details

- Fetch components from componentsStore on mount
- Issue count computed by filtering issuesStore by component_id
- Delete with force checkbox in confirmation modal
- Empty state when no components exist

### Expected File Paths

- `frontend/src/views/ComponentsView.vue`
- `frontend/src/components/component/ComponentCard.vue`
- `frontend/src/components/component/CreateComponentModal.vue`

### Business Value

Components organize issues into logical groups. Users need to create, manage, and navigate between components to keep their work organized.

## Status: COMPLETED
