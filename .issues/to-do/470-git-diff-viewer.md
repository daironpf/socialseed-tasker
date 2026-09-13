# Issue #470: Implement Git diff viewer in IssueDetailView Progress tab

## Description
Implement a code diff viewer component in the Progress tab's "Files Changed" section of `IssueDetailView`, showing side-by-side or unified diff views.

## Expected Behavior
- Diff viewer component styled like VS Code / GitHub (via `diff2html` or similar)
- Split view (side-by-side) and unified view toggle
- Color-coded lines: added (green), removed (red), modified
- Copy snippet and download patch (`.patch`) buttons
- Renders agent-provided diff content from agent logs

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Issue Detail / Diff Viewer

## Implementation Plan
1. Install `diff2html` for diff rendering
2. Create `DiffViewer.vue` component with split/unified toggle
3. Implement line highlighting (added/removed/modified)
4. Add copy-to-clipboard and download patch functionality
5. Integrate into IssueDetailView Progress tab "Files Changed" section
6. Parse agent log FILES type content into diff format

## Acceptance Criteria
- [ ] Diff viewer renders in Progress tab "Files Changed"
- [ ] Split view and unified view toggle
- [ ] Color-coded lines (green=added, red=removed, amber=modified)
- [ ] Copy snippet button
- [ ] Download `.patch` button
- [ ] Renders content from agent FILES logs

## Verification
- Open an issue with FILES agent logs
- Toggle between split and unified view
- Lines are color-coded correctly
- Copy button copies diff text
- Download produces valid `.patch` file

## Related Issues
- #469 (Rich text editor)
