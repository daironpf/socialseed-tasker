# Issue #469: Replace textarea with rich-text editor and Mermaid.js rendering

## Description
Replace the plain `textarea` in issue description and comments with a rich-text editor supporting slash commands (`/`) and dynamic Mermaid.js diagram rendering.

## Expected Behavior
- Rich-text editor in `IssueDetailView` Details tab description field
- Slash command menu on `/` (insert code, lists, tables, alerts, headings)
- Syntax highlighting in code blocks (Prism.js or Shiki)
- Auto-render Mermaid.js diagrams from ` ```mermaid ` code blocks
- Markdown output saved to backend (compatible with existing MarkdownRenderer)

## Status: COMPLETED

## Priority: MEDIUM

## Component
Frontend / Issue Detail / Editor

## Changes Made
1. Installed `mermaid` package for diagram rendering
2. Created `RichTextEditor.vue` component with toolbar and slash commands
3. Toolbar buttons: Bold, Italic, Code, H1, H2, H3, Divider, Preview toggle
4. Slash command menu (`/`) with 14 commands: headings, formatting, code blocks, mermaid diagrams, lists, tables, quotes
5. Keyboard navigation in slash menu: ArrowUp/Down, Enter, Esc
6. Tab key inserts 2 spaces
7. Live preview toggle with MarkdownRenderer
8. Updated `MarkdownRenderer.vue` to render Mermaid.js diagrams from ` ```mermaid ` code blocks
9. Mermaid initialized with theme detection (dark/light)
10. Integrated into IssueDetailView Details tab, replacing textarea
11. Added i18n keys for editor UI (EN/ES)
12. Output is valid markdown for backend storage

## Verification
- Typing `/` opens slash command menu
- Selecting "Mermaid Diagram" inserts mermaid code block
- Preview toggle shows rendered markdown with diagrams
- Saved content is valid markdown
- Existing MarkdownRenderer still works for read-only display
- Toolbar buttons insert formatting syntax

## Related Issues
- #471 (Git diff viewer)
