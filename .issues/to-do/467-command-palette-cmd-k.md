# Issue #467: Implement universal command palette (Cmd+K / Ctrl+K)

## Description
Implement a global floating modal activated by `Cmd+K` or `Ctrl+K` for quick search and execution of actions across the entire application.

## Expected Behavior
- Pressing `Cmd+K` or `Ctrl+K` opens a centered search modal overlay
- Fuzzy search in real-time across: system pages, issues (by title/ID), components, and quick actions (e.g. "Create Issue", "Toggle Dark Mode")
- Keyboard navigation: Arrow Up/Down to select, Enter to execute, Esc to close
- Recent actions registry for automatic suggestions when palette opens
- Modal closes on click-outside or Esc key

## Status: PENDING

## Priority: HIGH

## Component
Frontend / UX / Command Palette

## Implementation Plan
1. Create `CommandPalette.vue` component in `src/components/ui/`
2. Register global `keydown` listener for `Cmd+K` / `Ctrl+K`
3. Build fuzzy search logic across pages, issues, components, and actions
4. Implement keyboard navigation (ArrowUp, ArrowDown, Enter, Esc)
5. Add recent actions tracking via localStorage
6. Integrate into `App.vue` as a global overlay
7. Add i18n keys for palette UI strings

## Acceptance Criteria
- [ ] Listens for global `keydown` event for `Cmd+K` / `Ctrl+K`
- [ ] Fuzzy search across pages, issues, components, and quick actions
- [ ] Keyboard navigation (ArrowUp/Down, Enter, Esc)
- [ ] Recent actions registry persisted in localStorage
- [ ] Click-outside to close
- [ ] i18n support (EN/ES)

## Verification
- Press Cmd+K / Ctrl+K opens the palette
- Typing filters results in real-time
- Arrow keys navigate, Enter executes, Esc closes
- Recent actions appear as suggestions
- Works from any page in the app

## Related Issues
- #470 (Global keyboard shortcuts system)
