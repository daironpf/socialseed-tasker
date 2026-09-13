# Issue #467: Implement universal command palette (Cmd+K / Ctrl+K)

## Description
Implement a global floating modal activated by `Cmd+K` or `Ctrl+K` for quick search and execution of actions across the entire application.

## Expected Behavior
- Pressing `Cmd+K` or `Ctrl+K` opens a centered search modal overlay
- Fuzzy search in real-time across: system pages, issues (by title/ID), components, and quick actions (e.g. "Create Issue", "Toggle Dark Mode")
- Keyboard navigation: Arrow Up/Down to select, Enter to execute, Esc to close
- Recent actions registry for automatic suggestions when palette opens
- Modal closes on click-outside or Esc key

## Status: COMPLETED

## Priority: HIGH

## Component
Frontend / UX / Command Palette

## Changes Made
1. Created `CommandPalette.vue` component in `src/components/ui/`
2. Global `keydown` listener for `Cmd+K` / `Ctrl+K` with toggle behavior
3. Fuzzy search across pages (10 routes), issues (from store), components (from store), and quick actions (4 actions)
4. Keyboard navigation: ArrowUp/Down to move, Enter to execute, Esc to close
5. Recent actions tracking via localStorage (persists last 10, shows top 5)
6. Integrated into `App.vue` as a global overlay
7. Added i18n keys for palette UI strings (EN/ES)
8. Categories: Pages, Quick Actions, Issues, Components
9. Quick actions: Create Issue, Toggle Dark Mode, Toggle Sidebar, Clear Filters
10. Visual feedback: highlighted selection, status-colored issue icons, category labels

## Verification
- Cmd+K / Ctrl+K opens the palette from any page
- Typing filters results with fuzzy matching
- Arrow keys navigate, Enter executes, Esc closes
- Recent actions appear as suggestions when palette opens empty
- Click-outside closes the palette
- i18n works in both EN and ES

## Related Issues
- #470 (Global keyboard shortcuts system)
