# Issue #500: Add GitHub Sync Widget to Issue Detail View

## Description
Issues can be mirrored to GitHub via Causal Mirroring. The `IssueDetailView` must include a `GitHubSyncCard` showing the linked GitHub issue number, URL, sync status badge, and a mock re-sync button.

## Status: DONE

## Priority: MEDIUM

## Component
Frontend / Issue Detail / GitHub Integration

## Implementation
1. Added `GitHubSync` interface to `types/index.ts`
2. Added `github_sync?` optional field to `Issue` interface
3. Added `github_sync` data to all 100 mock issues in `issues.json` (alternating SYNCED/PENDING_PUSH/ERROR)
4. Created `GitHubSyncCard.vue` with:
   - Clickable issue number linking to GitHub
   - Color-coded sync status badge (green=SYNCED, yellow=PENDING_PUSH, red=ERROR)
   - Last synced timestamp
   - "Force Re-sync" button with spinner animation
5. Embedded `GitHubSyncCard` in IssueDetailView Details tab (conditionally shown if `issue.github_sync` exists)
6. Added i18n keys for GitHub sync section (EN + ES)

## Acceptance Criteria
- [x] GitHub sync data present in mock issues
- [x] `GitHubSyncCard` component created with issue link, status badge, re-sync button
- [x] Card embedded in IssueDetailView Details tab
- [x] Issue number links to external GitHub URL
- [x] Sync status badge shows correct color per status
- [x] "Force Re-sync" button simulates status change
- [x] i18n support (EN + ES)

## Files Created
- `frontend/src/components/issue/GitHubSyncCard.vue`

## Files Modified
- `frontend/src/types/index.ts` — added GitHubSync interface, extended Issue
- `frontend/src/dataset-de-pruebas/issues.json` — added github_sync to all 100 issues
- `frontend/src/views/IssueDetailView.vue` — embedded GitHubSyncCard, added import and handler
- `frontend/src/locales/en.json` — added githubSync section (6 keys)
- `frontend/src/locales/es.json` — added githubSync section (6 keys)

## Related Issues
- #90 (Causal Mirroring), #89 (Bidirectional Webhook)
