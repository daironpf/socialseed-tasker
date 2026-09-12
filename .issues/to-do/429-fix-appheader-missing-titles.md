# Issue #429: Fix AppHeader missing page titles

## Description
The `AppHeader.vue` component has a `titles` map that maps route paths to display titles. Several routes are missing from this map, causing them to default to "Dashboard" regardless of their actual purpose.

## Expected Behavior
Each route should show its correct title in the header:
- `/system` → "System Dashboard"
- `/constraints` → "Constraints"
- `/users` → "Users"
- `/analysis` → "Analysis"

## Actual Behavior
All four routes display "Dashboard" as the header title.

## Steps to Reproduce
1. Navigate to `/system` — header shows "Dashboard"
2. Navigate to `/constraints` — header shows "Dashboard"
3. Navigate to `/users` — header shows "Dashboard"
4. Navigate to `/analysis` — header shows "Dashboard"

## Status: OPEN

## Priority: LOW

## Component
Frontend / `src/components/layout/AppHeader.vue`

## Suggested Fix
Add missing entries to the `titles` object:
```typescript
const titles: Record<string, string> = {
  '/board': 'Dashboard',
  '/system': 'System Dashboard',
  '/kanban': 'Kanban',
  '/list': 'Issues',
  '/graph': 'Graph',
  '/components': 'Components',
  '/policies': 'Policies',
  '/constraints': 'Constraints',
  '/users': 'Users',
  '/analysis': 'Analysis',
}
```

## Impact
Minor UX confusion — users see incorrect page titles.

## Related Issues
(none)
