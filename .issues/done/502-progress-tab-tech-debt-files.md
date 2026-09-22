# Issue #502: Add Tech Debt and Affected Files to ProgressTab

## Description
The ProgressTab in `IssueDetailView.vue` must display the AI-generated Progress Manifest: modified file paths with change-type badges, and technical debt notes rendered in Markdown with alert styling.

## Status: DONE

## Priority: MEDIUM

## Component
Frontend / Issue Detail / ProgressTab

## Implementation
1. Added `AffectedFile` interface to `types/index.ts` with `path` and `change_type` fields
2. Added `affected_files?` and `technical_debt_notes?` optional fields to `Issue` interface
3. Added `affected_files` and `technical_debt_notes` data to all 100 mock issues in `issues.json`
4. Updated ProgressTab in `IssueDetailView.vue`:
   - **Affected Files section**: list file paths with color-coded badges (green=CREATED, blue=EDITED, red=DELETED)
   - **Technical Debt section**: amber container with Markdown-rendered notes
   - Empty state messages when no files or debt notes
5. Added i18n keys for progress tab sections (EN + ES)

## Acceptance Criteria
- [x] Affected files data present in mock issues
- [x] Technical debt notes data present in mock issues
- [x] Affected files rendered as list with change-type badges
- [x] Technical debt rendered as Markdown in styled container
- [x] Empty state when no files or debt notes
- [x] i18n support (EN + ES)

## Files Modified
- `frontend/src/types/index.ts` — added AffectedFile interface, extended Issue
- `frontend/src/dataset-de-pruebas/issues.json` — added affected_files and technical_debt_notes to all 100 issues
- `frontend/src/views/IssueDetailView.vue` — updated ProgressTab with Affected Files and Tech Debt sections
- `frontend/src/locales/en.json` — added affectedFiles, noAffectedFiles, techDebtNotes, changeType keys
- `frontend/src/locales/es.json` — added affectedFiles, noAffectedFiles, techDebtNotes, changeType keys

## Related Issues
- #47 (Issue Detail Panel), #496 (PII Guard)
