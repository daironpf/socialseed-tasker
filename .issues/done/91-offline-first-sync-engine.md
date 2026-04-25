# Issue #91: Offline-First Sync Engine

## Description

Implement queue system to batch local changes and push them to GitHub once internet connection is restored. Critical for intermittent connectivity scenarios.

## Requirements

- Create local sync queue in Neo4j
- Queue operations when offline (create, update, delete)
- Detect network availability via health check
- Batch queue and push when online
- Handle conflict resolution (local vs remote wins)
- Add retry with exponential backoff for failed syncs
- Provide CLI commands to view/manage queue: `tasker sync status`, `tasker sync force`

## Technical Details

### Sync Queue Structure
```python
class SyncQueueItem(BaseModel):
    id: UUID
    operation: str  # "create", "update", "delete"
    entity_type: str  # "issue", "comment", "label"
    entity_id: UUID
    payload: dict
    created_at: datetime
    retry_count: int = 0
    status: str  # "pending", "processing", "failed"
```

### API Endpoints
- `GET /sync/queue` - View pending sync items
- `POST /sync/force` - Force sync attempt
- `GET /sync/status` - Get sync status (online/offline, queue size)

### Configuration
- `SYNC_BATCH_SIZE` - Max items per sync batch (default: 50)
- `SYNC_RETRY_DELAY` - Base delay between retries (seconds)

## Business Value

Enables use in disconnected environments. Agents can continue working offline and changes sync when connectivity returns.

## Status: COMPLETED