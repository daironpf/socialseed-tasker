# Issue #09: Implement Local Files Storage Fallback

## Description

Build the local file storage backend in `src/socialseed_tasker/storage/local_files/`. This serves as a fallback for offline/low-resource environments where Neo4j is not available, ensuring the system remains functional without a graph database.

### Requirements

#### Module Structure

**`file_store.py`** - File I/O utilities
- Read/write JSON files with atomic operations (write to temp, then rename)
- Directory management for data storage
- File locking for concurrent access safety
- Backup/restore utilities

**`repositories.py`** - Repository implementations
- `FileTaskRepository` implementing `TaskRepositoryInterface`
- `FileComponentRepository` implementing component operations

#### Storage Format

**Directory Structure:**
```
.tasker-data/
  components/
    {component_id}.json
  issues/
    {issue_id}.json
  relationships/
    {issue_id}_depends_on_{depends_on_id}.json
    {issue_id}_blocks_{blocked_id}.json
    {issue_id}_affects_{affected_id}.json
  metadata.json
```

**Issue JSON Format:**
```json
{
  "id": "uuid-string",
  "title": "Issue title",
  "description": "Markdown description",
  "status": "OPEN",
  "priority": "MEDIUM",
  "component_id": "uuid-string",
  "labels": ["bug", "urgent"],
  "architectural_constraints": [],
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "closed_at": null
}
```

**Relationship JSON Format:**
```json
{
  "type": "DEPENDS_ON",
  "source_id": "uuid-string",
  "target_id": "uuid-string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Repository Implementation Requirements

**FileTaskRepository:**
- `create_issue()` - Serialize issue to JSON file
- `get_issue()` - Read and deserialize JSON file
- `update_issue()` - Read, merge updates, write back atomically
- `close_issue()` - Update status and closed_at
- `delete_issue()` - Delete issue file and related relationship files
- `list_issues()` - Scan directory, deserialize all matching files
- `add_dependency()` - Create relationship JSON file
- `remove_dependency()` - Delete relationship JSON file
- `get_dependencies()` - Scan relationship files for source matches
- `get_dependents()` - Scan relationship files for target matches
- `get_dependency_chain()` - BFS/DFS traversal using relationship files
- `detect_circular_dependency()` - Graph traversal to detect cycles

**FileComponentRepository:**
- `create_component()` - Serialize component to JSON file
- `get_component()` - Read and deserialize JSON file
- `list_components()` - Scan directory, deserialize all files

#### Performance Considerations
- Implement in-memory caching for frequently accessed data
- Cache invalidation on write operations
- Batch operations where possible (read all files once for list operations)
- Consider SQLite as an alternative for larger local datasets (document as future enhancement)

#### Offline Mode Detection
- Auto-detect when Neo4j is unavailable
- Graceful fallback to file storage
- Sync mechanism to migrate file data to Neo4j when it becomes available (future enhancement)

### Requirements
- All file storage code stays in `storage/local_files/`
- Must implement the `TaskRepositoryInterface` from core exactly
- No business logic in the storage layer - only data access
- Atomic write operations to prevent data corruption
- Proper file locking for concurrent access
- Human-readable JSON files for easy manual inspection

### Business Value

The local file storage ensures the system remains functional in offline environments, CI pipelines without Neo4j, or resource-constrained scenarios. It also serves as an excellent testing backend and provides a data migration path. The identical interface means switching between storage backends requires zero changes to core logic or entrypoints.

## Status: COMPLETED
