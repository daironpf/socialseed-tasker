# Issue #500: Add GitHub Sync Widget to Issue Detail View

## Description
Issues can be mirrored to GitHub via Causal Mirroring. The `IssueDetailView` must include a `GitHubSyncCard` showing the linked GitHub issue number, URL, sync status badge, and a mock re-sync button.

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / Issue Detail / GitHub Integration

## Implementation
1. Add `github_sync` object to mock issue data in `mockApi.ts`:
   ```json
   "github_sync": {
     "issue_number": 88,
     "github_url": "https://github.com/daironpf/socialseed-tasker/issues/88",
     "sync_status": "SYNCED",
     "last_synced_at": "2026-04-26T14:30:00Z"
   }
   ```
2. Add `github_sync` type to Issue interface in `types/index.ts`
3. Create `GitHubSyncCard.vue` component:
   - Issue number as clickable external link (#88)
   - Sync status badge (SYNCED=green, PENDING_PUSH=yellow, ERROR=red)
   - Last synced timestamp
   - "Force Re-sync" button (mock: toggles status temporarily)
4. Embed `GitHubSyncCard` in `IssueDetailView.vue` Details tab
5. Add i18n keys for GitHub sync section

## Acceptance Criteria
- [ ] GitHub sync data present in mock issues
- [ ] `GitHubSyncCard` component created with issue link, status badge, re-sync button
- [ ] Card embedded in IssueDetailView Details tab
- [ ] Issue number links to external GitHub URL
- [ ] Sync status badge shows correct color per status
- [ ] "Force Re-sync" button simulates status change
- [ ] i18n support (EN + ES)

## Verification
- Open IssueDetailView for any issue
- See GitHub Sync card in Details tab with issue number link
- Click issue number -> opens GitHub URL in new tab
- Sync status badge shows green (SYNCED)
- Click "Force Re-sync" -> badge cycles through states
- Last synced timestamp displayed

## Files to Create
- `frontend/src/components/issue/GitHubSyncCard.vue`

## Files to Modify
- `frontend/src/types/index.ts` — add GitHubSync interface, extend Issue
- `frontend/src/api/mockApi.ts` — add github_sync to mock issues
- `frontend/src/views/IssueDetailView.vue` — embed GitHubSyncCard
- `frontend/src/locales/en.json` — add github sync keys
- `frontend/src/locales/es.json` — add github sync keys

## Related Issues
- #90 (Causal Mirroring), #89 (Bidirectional Webhook)
