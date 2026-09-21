# Issue #499: Add Network Status Banner and Sync Queue Indicator

## Description
Users need visual feedback on connection state and pending sync queue status. A `SyncStatusBadge` component must show SYNCED/OFFLINE_QUEUED/SYNCING states with a pending count, updating in real-time when local changes occur.

## Status: TODO

## Priority: MEDIUM

## Component
Frontend / UI / Sync Status

## Implementation
1. Extend `uiStore.ts` with `connectionState: 'SYNCED' | 'OFFLINE_QUEUED' | 'SYNCING'` and `pendingSyncCount: number`
2. Create `SyncStatusBadge.vue` component with color-coded indicators:
   - Green dot: "Synced"
   - Yellow dot: "Offline ({count} pending)"
   - Blue animated dot: "Syncing..."
3. Place `SyncStatusBadge` in `AppHeader.vue` next to the project selector
4. Simulate transitions: on create/edit/kanban move, set `OFFLINE_QUEUED`, increment count, after 2s set `SYNCED` and reset count
5. Add i18n keys for all states

## Acceptance Criteria
- [ ] `SyncStatusBadge` component created and placed in AppHeader
- [ ] Green indicator shown when synced
- [ ] Yellow indicator with pending count shown after local mutation
- [ ] Blue animated indicator shown during simulated sync
- [ ] Status transitions automatically after 2 seconds
- [ ] Badge reflects real-time state on every CRUD operation
- [ ] i18n support (EN + ES)

## Verification
- Create a new issue -> badge turns yellow with "1 pending"
- Wait 2 seconds -> badge turns green "Synced"
- Edit an issue -> badge turns yellow with "1 pending"
- Move a Kanban card -> badge turns yellow
- Badge animates blue briefly during sync simulation

## Files to Create
- `frontend/src/components/ui/SyncStatusBadge.vue`

## Files to Modify
- `frontend/src/stores/uiStore.ts` — add connectionState, pendingSyncCount, mutations
- `frontend/src/components/layout/AppHeader.vue` — add SyncStatusBadge
- `frontend/src/locales/en.json` — add sync status keys
- `frontend/src/locales/es.json` — add sync status keys

## Related Issues
- #498 (Project Selector), #475 (Notification Center)
