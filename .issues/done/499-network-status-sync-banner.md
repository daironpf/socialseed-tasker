# Issue #499: Add Network Status Banner and Sync Queue Indicator

## Description
Users need visual feedback on connection state and pending sync queue status. A `SyncStatusBadge` component must show SYNCED/OFFLINE_QUEUED/SYNCING states with a pending count, updating in real-time when local changes occur.

## Status: DONE

## Priority: MEDIUM

## Component
Frontend / UI / Sync Status

## Implementation
1. Extended `uiStore.ts` with `connectionState: 'SYNCED' | 'OFFLINE_QUEUED' | 'SYNCING'` and `pendingSyncCount: number`
2. Added `simulateSync()` action that transitions: OFFLINE_QUEUED -> SYNCING -> SYNCED
3. Created `SyncStatusBadge.vue` with color-coded indicators and animated ping effect
4. Placed `SyncStatusBadge` in `AppHeader.vue` between ProjectSelector and NotificationCenter
5. Integrated `simulateSync()` calls in ListView, KanbanView, and GraphView after every CRUD operation
6. Added i18n keys for all states (EN + ES)

## Acceptance Criteria
- [x] `SyncStatusBadge` component created and placed in AppHeader
- [x] Green indicator shown when synced
- [x] Yellow indicator with pending count shown after local mutation
- [x] Blue animated indicator shown during simulated sync
- [x] Status transitions automatically after 2 seconds
- [x] Badge reflects real-time state on every CRUD operation
- [x] i18n support (EN + ES)

## Verification
- Create a new issue -> badge turns yellow with "1 pending"
- Wait 2 seconds -> badge turns blue "Syncing...", then green "Synced"
- Edit an issue -> badge turns yellow
- Move a Kanban card -> badge turns yellow
- Badge animates blue briefly during sync simulation

## Files Created
- `frontend/src/components/ui/SyncStatusBadge.vue`

## Files Modified
- `frontend/src/stores/uiStore.ts` — added connectionState, pendingSyncCount, simulateSync()
- `frontend/src/components/layout/AppHeader.vue` — added SyncStatusBadge import and placement
- `frontend/src/views/ListView.vue` — added simulateSync() after create/update/delete/close
- `frontend/src/views/KanbanView.vue` — added simulateSync() after drop/update/delete/close/create
- `frontend/src/views/GraphView.vue` — added uiStore import and simulateSync() after update/delete/close
- `frontend/src/locales/en.json` — added sync section (3 keys)
- `frontend/src/locales/es.json` — added sync section (3 keys)

## Related Issues
- #498 (Project Selector), #475 (Notification Center)
