# Issue #45: Build the main Kanban Board view

## Description

Create the primary Kanban-style board view that displays issues organized by status columns. This is the default landing page of the application.

### Requirements

- Create `frontend/src/views/BoardView.vue`
- Display 4 columns for each status: OPEN, IN_PROGRESS, BLOCKED, CLOSED
- Each column shows issue cards sorted by priority (CRITICAL first)
- Issue cards in the board show:
  - Title (truncated if too long)
  - Priority badge
  - Labels (first 3, with "+N" overflow indicator)
  - Component name (if available)
  - Dependency indicator (icon if has dependencies)
- Support drag-and-drop to change issue status between columns
- Column headers show issue count
- Clicking an issue card opens the detail panel/modal
- Loading skeleton while data is being fetched
- Empty state message when a column has no issues

### Technical Details

- Use HTML5 drag-and-drop API or a lightweight library like `@vueuse/gesture`
- On drop, call `updateIssue(id, { status: newStatus })` via the store
- Optimistic UI update: update local state immediately, revert on API error
- Responsive: on mobile, columns stack vertically or become horizontally scrollable
- Apply current filters from uiStore (search, component, priority)

### Expected File Paths

- `frontend/src/views/BoardView.vue`
- `frontend/src/components/board/KanbanColumn.vue`
- `frontend/src/components/board/IssueCard.vue`

### Business Value

The Kanban board provides an at-a-glance view of all work items, enabling teams to quickly identify bottlenecks, blocked issues, and progress.

## Status: COMPLETED
