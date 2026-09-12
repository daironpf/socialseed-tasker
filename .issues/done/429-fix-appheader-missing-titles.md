# Issue #429: Fix AppHeader missing page titles

## Description
The `AppHeader.vue` component has a `titles` map that maps route paths to display titles. Several routes are missing from this map, causing them to default to "Dashboard" regardless of their actual purpose.

## Expected Behavior
Each route should show its correct title in the header:
- `/system` → "System Dashboard"
- `/constraints` → "Constraints"
- `/users` → "Usuarios"
- `/analysis` → "Análisis"

## Actual Behavior
All four routes displayed "Dashboard" as the header title.

## Status: COMPLETED

## Priority: LOW

## Component
Frontend / `src/components/layout/AppHeader.vue`

## Changes Made
Added missing entries to the `titles` object:
- `/system`: "System Dashboard"
- `/constraints`: "Constraints"
- `/users`: "Usuarios"
- `/analysis`: "Análisis"

## Verification
- `/system` now shows "System Dashboard"
- `/constraints` now shows "Constraints"
- `/users` now shows "Usuarios"
- `/analysis` now shows "Análisis"

## Related Issues
(none)
