# Issue #470: Implement Git diff viewer in IssueDetailView Progress tab

## Description
Implement a code diff viewer component in the Progress tab's "Files Changed" section of `IssueDetailView`, showing side-by-side or unified diff views.

## Expected Behavior
- Diff viewer component styled like VS Code / GitHub (via `diff2html` or similar)
- Split view (side-by-side) and unified view toggle
- Color-coded lines: added (green), removed (red), modified
- Copy snippet and download patch (`.patch`) buttons
- Renders agent-provided diff content from agent logs

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Issue Detail / Diff Viewer

## Changes Made
1. Created `DiffViewer.vue` component with custom lightweight diff rendering (no heavy dependencies)
2. Unified view: shows old/new line numbers, +/- indicators, color-coded lines
3. Split view: side-by-side panels with aligned lines, empty rows for adds/removes
4. Parses unified diff format with `@@` hunk headers
5. Color coding: green for added, red for removed, amber for context
6. Copy-to-clipboard button with success feedback
7. Download `.patch` button with auto-naming
8. Statistics bar showing +/- counts
9. Integrated into IssueDetailView Progress tab "Files Changed" section
10. Added i18n keys for diff UI (EN/ES)

## Verification
- Open an issue with FILES agent logs
- Diff viewer renders with proper formatting
- Toggle between split and unified view works
- Lines are color-coded correctly (green/red)
- Copy button copies diff text to clipboard
- Download produces valid `.patch` file

## Related Issues
- #469 (Rich text editor)
