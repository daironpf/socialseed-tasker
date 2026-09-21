# Issue #502: Add Tech Debt and Affected Files to ProgressTab

## Description
The ProgressTab in `IssueDetailView.vue` must display the AI-generated Progress Manifest: modified file paths with change-type badges, and technical debt notes rendered in Markdown with alert styling.

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Issue Detail / ProgressTab

## Implementation
1. Add `affected_files` and `technical_debt_notes` fields to mock issue data in `mockApi.ts`:
   - `affected_files`: array of `{ path: string, change_type: 'CREATED' | 'EDITED' | 'DELETED' }`
   - `technical_debt_notes`: Markdown string with debt observations
2. Extend Issue type in `types/index.ts` with AffectedFile interface
3. Update ProgressTab rendering (inside IssueDetailView):
   - **Affected Files section**: list file paths with colored badges (green=CREATED, blue=EDITED, red=DELETED)
   - **Technical Debt section**: amber/red background container, renders Markdown with MarkdownRenderer
4. Populate mock data with realistic file paths and debt notes
5. Add i18n keys for progress tab sections

## Acceptance Criteria
- [ ] Affected files data present in mock issues
- [ ] Technical debt notes data present in mock issues
- [ ] Affected files rendered as list with change-type badges
- [ ] Technical debt rendered as Markdown in styled container
- [ ] Empty state when no files or debt notes
- [ ] i18n support (EN + ES)

## Verification
- Open IssueDetailView -> Progress tab
- See "Affected Files" section with file paths and colored badges
- See "Technical Debt" section with Markdown-rendered notes in amber container
- Issue without affected files -> shows "No files affected" message
- Issue without debt notes -> shows "No technical debt recorded" message
- File paths are readable, badges correctly colored

## Files to Create
- (none)

## Files to Modify
- `frontend/src/types/index.ts` — add AffectedFile interface, extend Issue
- `frontend/src/api/mockApi.ts` — add affected_files and technical_debt_notes to mock issues
- `frontend/src/views/IssueDetailView.vue` — update ProgressTab section
- `frontend/src/locales/en.json` — add progress tab keys
- `frontend/src/locales/es.json` — add progress tab keys

## Related Issues
- #47 (Issue Detail Panel), #496 (PII Guard)
