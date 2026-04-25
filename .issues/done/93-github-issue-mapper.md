# Issue #93: GitHubIssueMapper Domain Service

## Description

Implement domain service to map Neo4j UUIDs to GitHub Issue numbers and metadata. This service provides a consistent interface for looking up GitHub issue information from Tasker IDs.

## Requirements

- Create `GitHubIssueMapper` service in `core/services/`
- Implement methods: `get_github_issue_from_tasker_id()`, `get_tasker_id_from_github_issue()`
- Cache GitHub API responses (configurable TTL)
- Handle rate limiting gracefully
- Support bulk mapping for multiple IDs
- Track mapping history for audit

## Technical Details

### Service Interface
```python
class GitHubIssueMapper(Protocol):
    def get_github_url(self, tasker_issue_id: UUID) -> str | None: ...
    def get_github_number(self, tasker_issue_id: UUID) -> int | None: ...
    def get_tasker_id(self, github_issue_number: int) -> UUID | None: ...
    def bulk_map(self, tasker_ids: list[UUID]) -> dict[UUID, int]: ...
```

### Caching
- Use in-memory cache with TTL (default: 5 minutes)
- Invalidate cache on webhook events
- Cache miss: fetch from GitHub API

## Business Value

Provides reliable UUID<->GitHubNumber mapping needed by other GitHub integration features.

## Status: COMPLETED