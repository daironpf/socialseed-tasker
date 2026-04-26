"""ID resolution utilities for CLI."""

from __future__ import annotations

from uuid import UUID

from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface


def resolve_component_id(partial_id: str, repo: TaskRepositoryInterface) -> UUID:
    """Resolve a partial component ID to a full UUID.

    Args:
        partial_id: Full UUID or partial (at least 4 characters) or name (exact match)
        repo: Task repository to search

    Returns:
        Full UUID

    Raises:
        ValueError: If ID format is invalid or not found
    """
    from uuid import UUID

    # Try full UUID first
    try:
        return UUID(partial_id)
    except ValueError:
        pass

    # Minimum 4 characters for partial lookup OR exact name match
    if len(partial_id) < 4:
        raise ValueError(f"Invalid component ID format: {partial_id}. Need at least 4 characters.")

    # Try to find by exact name match first (names can be short)
    try:
        comp = repo.get_component_by_name(partial_id)
        if comp:
            return comp.id
    except Exception:
        pass

    # Search for matching component by prefix (UUID-like patterns need 8+)
    if len(partial_id) >= 8:
        components = repo.list_components(project=None)
        for comp in components:
            comp_id_str = str(comp.id)
            if comp_id_str.startswith(partial_id):
                return comp.id

    raise ValueError(f"Component not found: {partial_id}")


def resolve_issue_id(partial_id: str, repo: TaskRepositoryInterface) -> UUID:
    """Resolve a partial issue ID to a full UUID.

    Args:
        partial_id: Full UUID, partial UUID (4+ chars), or title (any length)
        repo: Task repository to search

    Returns:
        Full UUID

    Raises:
        ValueError: If ID format is invalid or not found
    """
    from uuid import UUID

    # Try full UUID first
    try:
        return UUID(partial_id)
    except ValueError:
        pass

    # Get all issues once
    issues = repo.list_issues(status=None, project=None)

    # Try exact title match first (no length restriction - titles can be short)
    for issue in issues:
        if issue.title.lower() == partial_id.lower():
            return issue.id

    # Minimum 4 characters for partial UUID lookup
    if len(partial_id) < 4:
        raise ValueError(f"Invalid issue ID format: {partial_id}. Need at least 4 characters for UUID lookup.")

    # Search for matching issue by prefix (4+ chars)
    for issue in issues:
        issue_id_str = str(issue.id)
        if issue_id_str.startswith(partial_id):
            return issue.id

    raise ValueError(f"Issue not found: {partial_id}")