# Issue #468: Create composable for global keyboard shortcuts

## Description
Create a `useKeyboardShortcuts` composable in Vue to capture universal single-character or key-sequence shortcuts for navigation and actions.

## Expected Behavior
- Shortcuts are ignored when focus is inside text fields (`input`, `textarea`, `contenteditable`)
- Global navigation keys: `C` (open create issue modal), `G`+`I` (go to ListView), `G`+`K` (go to Kanban), `G`+`G` (go to GraphView)
- Contextual keys in list/kanban: `J`/`K` (move focus between cards), `Enter` (open detail), `Esc` (close panels)
- Helper modal (`?`) listing all available shortcuts
- Key sequences with timeout (e.g. `G` then `I` within 1s)

## Status: PENDING

## Priority: HIGH

## Component
Frontend / UX / Keyboard Navigation

## Implementation Plan
1. Create `src/composables/useKeyboardShortcuts.ts`
2. Implement shortcut registry with scope-based activation (global vs contextual)
3. Add focus detection to ignore shortcuts in input fields
4. Create `KeyboardShortcutsHelp.vue` modal component
5. Integrate composable into views (ListView, KanbanView, GraphView)
6. Add i18n keys for shortcut descriptions

## Acceptance Criteria
- [ ] Composable `useKeyboardShortcuts` created with registry pattern
- [ ] Shortcuts ignored when focus is in input/textarea
- [ ] Global nav: `C`, `G`+`I`, `G`+`K`, `G`+`G`
- [ ] Contextual: `J`/`K` focus, `Enter` open, `Esc` close
- [ ] `?` opens shortcuts help modal
- [ ] Key sequences with timeout support
- [ ] i18n support for shortcut labels

## Verification
- `C` opens create issue modal from any page
- `G` then `I` navigates to list view
- `J`/`K` move focus in kanban cards
- `?` shows help modal with all shortcuts
- Shortcuts don't fire when typing in inputs

## Related Issues
- #467 (Command palette)
