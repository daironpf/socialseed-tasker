# Issue #468: Create composable for global keyboard shortcuts

## Description
Create a `useKeyboardShortcuts` composable in Vue to capture universal single-character or key-sequence shortcuts for navigation and actions.

## Expected Behavior
- Shortcuts are ignored when focus is inside text fields (`input`, `textarea`, `contenteditable`)
- Global navigation keys: `C` (open create issue modal), `G`+`I` (go to ListView), `G`+`K` (go to Kanban), `G`+`G` (go to GraphView)
- Contextual keys in list/kanban: `J`/`K` (move focus between cards), `Enter` (open detail), `Esc` (close panels)
- Helper modal (`?`) listing all available shortcuts
- Key sequences with timeout (e.g. `G` then `I` within 1s)

## Status: COMPLETED

## Priority: HIGH

## Component
Frontend / UX / Keyboard Navigation

## Changes Made
1. Created `src/composables/useKeyboardShortcuts.ts` with registry pattern
2. Shortcut registry supports `global` and `local` scopes
3. Focus detection ignores shortcuts when focus is in `input`, `textarea`, or `contenteditable`
4. Key sequence support with 1s timeout (e.g. `G` then `I`)
5. Created `KeyboardShortcutsHelp.vue` modal showing all shortcuts grouped by category
6. Integrated into `App.vue` with global shortcuts registered on mount
7. Added i18n keys for shortcut labels (EN/ES)
8. Global shortcuts: `C` (create issue), `G+I` (list), `G+K` (kanban), `G+G` (graph), `G+B` (dashboard), `G+U` (users), `G+C` (components), `D` (dark mode), `?` (help)
9. Composable exported `register`, `unregister`, `unregisterAll` for view-level use
10. `initKeyboardShortcuts()` / `destroyKeyboardShortcuts()` for lifecycle management

## Verification
- `C` navigates to list view from any page
- `G` then `I` navigates to list view
- `G` then `K` navigates to kanban
- `?` opens shortcuts help modal
- Shortcuts don't fire when typing in inputs
- `Esc` closes the help modal

## Related Issues
- #467 (Command palette)
