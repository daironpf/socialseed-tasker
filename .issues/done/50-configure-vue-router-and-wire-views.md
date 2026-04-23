# Issue #50: Configure Vue Router and wire all views together

## Description

Set up Vue Router with all routes and wire the application navigation together.

### Requirements

- Configure `frontend/src/router/index.ts` with these routes:
  - `/` → BoardView (default, redirects to `/board`)
  - `/board` → BoardView (Kanban board)
  - `/list` → ListView (table view)
  - `/components` → ComponentsView
  - `/issue/:id` → IssueDetailView

- Navigation in AppHeader:
  - Logo/brand linking to `/board`
  - Tab links: Board, List, Components
  - Active route highlighting

- Wire the "New Issue" button in AppHeader to open CreateIssueModal
- Wire the view mode toggle (board ↔ list) in AppHeader
- Wire component filter in Sidebar to uiStore filters
- Handle 404 route with a simple "Not Found" view

### Technical Details

- Use Vue Router `createRouter` with `createWebHistory`
- Lazy-load views with dynamic imports (`() => import(...)`)
- Route transitions with Vue `<Transition>` for smooth navigation
- Scroll to top on route change

### Expected File Paths

- `frontend/src/router/index.ts`
- `frontend/src/views/NotFoundView.vue`
- Modifications to `frontend/src/components/layout/AppHeader.vue`
- Modifications to `frontend/src/App.vue`

### Business Value

Routing ties all the individual views together into a cohesive, navigable application with clean URLs that can be bookmarked and shared.

## Status: COMPLETED
