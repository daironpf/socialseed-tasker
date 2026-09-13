# Issue #469: Replace textarea with rich-text editor and Mermaid.js rendering

## Description
Replace the plain `textarea` in issue description and comments with a rich-text editor supporting slash commands (`/`) and dynamic Mermaid.js diagram rendering.

## Expected Behavior
- Rich-text editor in `IssueDetailView` Details tab description field
- Slash command menu on `/` (insert code, lists, tables, alerts, headings)
- Syntax highlighting in code blocks (Prism.js or Shiki)
- Auto-render Mermaid.js diagrams from ` ```mermaid ` code blocks
- Markdown output saved to backend (compatible with existing MarkdownRenderer)

## Status: PENDING

## Priority: MEDIUM

## Component
Frontend / Issue Detail / Editor

## Implementation Plan
1. Install `@tiptap/vue-3` and extensions (StarterKit, CodeBlock, Table, etc.)
2. Install `mermaid` for diagram rendering
3. Create `RichTextEditor.vue` component wrapping Tiptap
4. Implement slash command menu with fuzzy matching
5. Add Mermaid.js rendering in code blocks via MarkdownRenderer
6. Integrate into IssueDetailView Details tab
7. Ensure output is markdown-compatible for backend storage

## Acceptance Criteria
- [ ] Tiptap editor replaces textarea in issue description
- [ ] Slash command menu on `/` with contextual options
- [ ] Syntax highlighting in code blocks
- [ ] Mermaid.js diagrams auto-render from mermaid code blocks
- [ ] Output is valid markdown for backend storage
- [ ] i18n support for editor UI

## Verification
- Typing `/` opens command menu
- Selecting "Code Block" inserts formatted code block
- Writing ` ```mermaid graph TD; A-->B; ``` ` renders a diagram
- Saved content is valid markdown
- Existing MarkdownRenderer still works for read-only display

## Related Issues
- #471 (Git diff viewer)
