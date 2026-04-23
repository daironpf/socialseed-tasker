"""Task skill template - Function Calling bridge for AI Agents.

This module provides standardized functions that an external AI Agent
can import and use to interact with the SocialSeed Tasker REST API.
It does NOT import the Tasker core; all communication happens via HTTP.

Version: 0.8.0
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TASKER_API_URL = os.environ.get("TASKER_API_URL", "http://localhost:8000")
TASKER_API_KEY = os.environ.get("TASKER_API_KEY", "")


def _request(
    method: str,
    path: str,
    body: dict[str, Any] | None = None,
    params: dict[str, str] | None = None,
) -> dict:
    """Send an HTTP request to the Tasker API and return the parsed response."""
    url = f"{TASKER_API_URL}{path}"

    if params:
        query = "&".join(f"{k}={v}" for k, v in params.items() if v)
        url = f"{url}?{query}"

    headers = {"Content-Type": "application/json"}
    if TASKER_API_KEY:
        headers["X-API-Key"] = TASKER_API_KEY

    data = json.dumps(body).encode("utf-8") if body else None
    req = Request(url, data=data, headers=headers, method=method)

    try:
        with urlopen(req) as response:
            if response.status == 204:
                return {"data": None, "error": None, "meta": {}}
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return json.loads(exc.read().decode("utf-8"))
    except URLError as exc:
        return {
            "data": None,
            "error": {"code": "CONNECTION_ERROR", "message": str(exc.reason)},
            "meta": {},
        }


# =============================================================================
# COMPONENTS
# =============================================================================


def create_component(
    name: str,
    project: str,
    description: str | None = None,
    labels: list[str] | None = None,
) -> dict:
    """Create a new component to group issues.

    Args:
        name: Component name (e.g., "auth-service", "frontend")
        project: Project name (e.g., "social-network")
        description: Optional description
        labels: Optional tags

    Returns:
        {"data": {"id": "...", "name": "...", ...}, "error": None}
    """
    body: dict[str, Any] = {"name": name, "project": project}
    if description:
        body["description"] = description
    if labels:
        body["labels"] = labels
    return _request("POST", "/api/v1/components", body)


def list_components(project: str | None = None, name: str | None = None) -> dict:
    """List all components, optionally filtered.

    Args:
        project: Filter by project name
        name: Filter by exact component name

    Returns:
        {"data": {"items": [...], "total": N}, "error": None}
    """
    params: dict[str, str] = {}
    if project:
        params["project"] = project
    if name:
        params["name"] = name
    return _request("GET", "/api/v1/components", params=params)


def get_component(component_id: str) -> dict:
    """Get full details of a single component."""
    return _request("GET", f"/api/v1/components/{component_id}")


def update_component(component_id: str, data: dict[str, Any]) -> dict:
    """Update component fields."""
    return _request("PATCH", f"/api/v1/components/{component_id}", data)


def delete_component(component_id: str) -> dict:
    """Delete a component and all associated issues."""
    return _request("DELETE", f"/api/v1/components/{component_id}")


# =============================================================================
# ISSUES
# =============================================================================


def create_issue(
    title: str,
    component_id: str | None = None,
    description: str = "",
    priority: str = "MEDIUM",
    labels: list[str] | None = None,
    project: str | None = None,
) -> dict:
    """Create a new issue.

    Args:
        title: Issue title (1-200 chars)
        component_id: UUID of target component
        description: Markdown description
        priority: LOW, MEDIUM, HIGH, CRITICAL
        labels: Tags for categorisation

    Returns:
        {"data": {"id": "...", "title": "...", "status": "OPEN", ...}, "error": None}
    """
    body: dict[str, Any] = {"title": title, "priority": priority}
    if component_id:
        body["component_id"] = component_id
    if description:
        body["description"] = description
    if labels:
        body["labels"] = labels
    if project:
        body["project"] = project
    return _request("POST", "/api/v1/issues", body)


def list_issues(
    status: str | None = None,
    project: str | None = None,
    component: str | None = None,
    priority: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    """List issues with optional filters and pagination.

    Returns:
        {"data": {"items": [...], "total": N, "page": 1, "page_size": 50}}
    """
    params: dict[str, str] = {
        "page": str(page),
        "page_size": str(page_size),
    }
    if status:
        params["status"] = status
    if project:
        params["project"] = project
    if component:
        params["component"] = component
    if priority:
        params["priority"] = priority
    return _request("GET", "/api/v1/issues", params=params)


def get_issue(issue_id: str) -> dict:
    """Get full details of a single issue."""
    return _request("GET", f"/api/v1/issues/{issue_id}")


def update_issue(
    issue_id: str,
    status: str | None = None,
    priority: str | None = None,
    description: str | None = None,
    labels: list[str] | None = None,
    agent_working: bool | None = None,
) -> dict:
    """Partially update an issue's fields.

    Args:
        issue_id: Issue UUID
        status: OPEN, IN_PROGRESS, BLOCKED, CLOSED
        priority: LOW, MEDIUM, HIGH, CRITICAL
        description: Markdown description
        labels: List of labels
        agent_working: True if an AI agent is working on this

    Returns:
        {"data": {...}, "error": None}
    """
    body: dict[str, Any] = {}
    if status:
        body["status"] = status
    if priority:
        body["priority"] = priority
    if description is not None:
        body["description"] = description
    if labels:
        body["labels"] = labels
    if agent_working is not None:
        body["agent_working"] = agent_working
    return _request("PATCH", f"/api/v1/issues/{issue_id}", body)


def close_issue(issue_id: str) -> dict:
    """Close an issue. Fails if it has open dependencies."""
    return _request("POST", f"/api/v1/issues/{issue_id}/close")


def delete_issue(issue_id: str) -> dict:
    """Permanently delete an issue."""
    return _request("DELETE", f"/api/v1/issues/{issue_id}")


def get_workable_issues(
    priority: str | None = None,
    component: str | None = None,
) -> dict:
    """Get issues where all dependencies are closed (ready to work on).

    Returns:
        {"data": {"items": [...]}, "error": None}
    """
    params: dict[str, str] = {}
    if priority:
        params["priority"] = priority
    if component:
        params["component"] = component
    return _request("GET", "/api/v1/workable-issues", params=params)


# =============================================================================
# DEPENDENCIES
# =============================================================================


def add_dependency(issue_id: str, depends_on_id: str) -> dict:
    """Create a DEPENDS_ON relationship between two issues."""
    return _request("POST", f"/api/v1/issues/{issue_id}/dependencies", {"depends_on_id": depends_on_id})


def remove_dependency(issue_id: str, depends_on_id: str) -> dict:
    """Remove a DEPENDS_ON relationship."""
    return _request("DELETE", f"/api/v1/issues/{issue_id}/dependencies/{depends_on_id}")


def get_dependencies(issue_id: str) -> dict:
    """List issues that the given issue depends on."""
    return _request("GET", f"/api/v1/issues/{issue_id}/dependencies")


def get_dependency_chain(issue_id: str) -> dict:
    """Get the full transitive dependency chain for an issue."""
    return _request("GET", f"/api/v1/issues/{issue_id}/dependency-chain")


def get_blocked_issues() -> dict:
    """List all issues blocked by at least one open dependency."""
    return _request("GET", "/api/v1/blocked-issues")


def get_dependency_graph(project: str | None = None) -> dict:
    """Get full dependency graph for visualization.

    Returns:
        {"data": {"nodes": [...], "edges": [...]}}
    """
    params: dict[str, str] = {}
    if project:
        params["project"] = project
    return _request("GET", "/api/v1/graph/dependencies", params=params)


# =============================================================================
# ANALYSIS
# =============================================================================


def analyze_impact(issue_id: str) -> dict:
    """Analyze downstream impact of an issue.

    Returns:
        {"data": {"directly_affected": [...], "transitively_affected": [...], "risk_level": "HIGH"}}
    """
    return _request("GET", f"/api/v1/analyze/impact/{issue_id}")


def analyze_component_impact(component_id: str) -> dict:
    """Analyze impact for a component.

    Returns:
        {"data": {"total_issues": N, "criticality_score": 0.75, "risk_level": "MEDIUM"}}
    """
    return _request("GET", f"/api/v1/analyze/component-impact/{component_id}")


def analyze_root_cause(
    test_failure: str,
    component_id: str | None = None,
) -> dict:
    """Find likely root causes for a test failure.

    Args:
        test_failure: Description of the test failure
        component_id: Optional component UUID

    Returns:
        {"data": {"causal_links": [...]}}
    """
    body: dict[str, Any] = {"test_failure": test_failure}
    if component_id:
        body["component_id"] = component_id
    return _request("POST", "/api/v1/analyze/root-cause", body)


# =============================================================================
# PROJECT DASHBOARD
# =============================================================================


def get_project_summary(project_name: str) -> dict:
    """Get complete project summary dashboard.

    Returns:
        {"data": {"total_issues": N, "by_status": {...}, "dependency_health": 0.85, ...}}
    """
    return _request("GET", f"/api/v1/projects/{project_name}/summary")


# =============================================================================
# ADMIN & SYSTEM
# =============================================================================


def health_check() -> dict:
    """Check API and Neo4j health.

    Returns:
        {"data": {"status": "healthy", "version": "0.8.0", "neo4j": "connected"}}
    """
    return _request("GET", "/health")


def admin_reset(scope: str = "all") -> dict:
    """Reset data.

    Args:
        scope: "all", "issues", or "components"

    Returns:
        {"data": {"deleted_count": N}}
    """
    return _request("POST", "/api/v1/admin/reset", {"scope": scope})


# =============================================================================
# SYNC (GitHub Integration)
# =============================================================================


def get_sync_status() -> dict:
    """Get sync status.

    Returns:
        {"data": {"is_online": true, "queue_size": 0, "last_sync": "..."}}
    """
    return _request("GET", "/api/v1/sync/status")


def get_sync_queue() -> dict:
    """Get pending sync queue items."""
    return _request("GET", "/api/v1/sync/queue")


def force_sync() -> dict:
    """Force sync attempt."""
    return _request("POST", "/api/v1/sync/force")


def test_webhook() -> dict:
    """Test webhook configuration."""
    return _request("GET", "/api/v1/webhooks/github/test")
