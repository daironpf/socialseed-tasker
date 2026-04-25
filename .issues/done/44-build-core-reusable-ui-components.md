# Issue #44: Build core reusable UI components

## Description

Create the foundational reusable UI components that will be used across the application.

### Requirements

- Create `frontend/src/components/ui/` with these components:

  - `StatusBadge.vue` - Color-coded badge for issue status (OPEN=blue, IN_PROGRESS=amber, CLOSED=green, BLOCKED=red)
  - `PriorityBadge.vue` - Color-coded badge for priority (LOW=gray, MEDIUM=blue, HIGH=orange, CRITICAL=red)
  - `LabelTag.vue` - Small pill-style tag for issue labels
  - `Button.vue` - Reusable button component with variants (primary, secondary, danger, ghost)
  - `Input.vue` - Styled text input with label and error state
  - `Select.vue` - Styled dropdown select
  - `Textarea.vue` - Styled multiline text area
  - `Modal.vue` - Overlay modal with backdrop, header, body, footer slots
  - `Card.vue` - Card container with header, body, footer slots
  - `EmptyState.vue` - Illustration + message when no data exists
  - `LoadingSpinner.vue` - Animated spinner for loading states
  - `Toast.vue` - Notification toast for success/error messages

- Create `frontend/src/components/layout/`:
  - `AppHeader.vue` - Top navigation bar with logo, search bar, dark mode toggle
  - `Sidebar.vue` - Left sidebar with component filter, status filter, priority filter
  - `MainLayout.vue` - Layout wrapper with header + sidebar + content area

### Technical Details

- All components use `<script setup>` with TypeScript
- Use Tailwind CSS utility classes exclusively
- Support dark mode via Tailwind's `dark:` variant
- Components should be accessible (proper ARIA attributes, keyboard navigation)
- Use Vue slots for flexible content composition

### Expected File Paths

- `frontend/src/components/ui/StatusBadge.vue`
- `frontend/src/components/ui/PriorityBadge.vue`
- `frontend/src/components/ui/LabelTag.vue`
- `frontend/src/components/ui/Button.vue`
- `frontend/src/components/ui/Input.vue`
- `frontend/src/components/ui/Select.vue`
- `frontend/src/components/ui/Textarea.vue`
- `frontend/src/components/ui/Modal.vue`
- `frontend/src/components/ui/Card.vue`
- `frontend/src/components/ui/EmptyState.vue`
- `frontend/src/components/ui/LoadingSpinner.vue`
- `frontend/src/components/ui/Toast.vue`
- `frontend/src/components/layout/AppHeader.vue`
- `frontend/src/components/layout/Sidebar.vue`
- `frontend/src/components/layout/MainLayout.vue`

### Business Value

Reusable components ensure visual consistency, reduce code duplication, and speed up development of new features.

## Status: COMPLETED
