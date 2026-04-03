"""Task skill template - Function Calling bridge for AI Agents.

This module provides standardized functions that an external AI Agent
can import and use to interact with the SocialSeed Tasker REST API.
It does NOT import the Tasker core; all communication happens via HTTP.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

TASKER_API_URL = os.environ.get("TASKER_API_URL", "http://localhost:8000")


def _request(method: str, path: str, body: dict[str, Any] | None = None) -> dict:
    """Send an HTTP request to the Tasker API and return the parsed response."""
    url = f"{TASKER_API_URL}{path}"
    headers = {"Content-Type": "application/json"}
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


def create_issue(
    title: str,
    component_id: str,
    description: str = "",
    priority: str = "MEDIUM",
    labels: list[str] | None = None,
) -> dict:
    """Create a new issue in the Tasker system.

    Args:
        title: Issue title (1-200 characters).
        component_id: UUID of the target component.
        description: Detailed description in Markdown.
        priority: LOW, MEDIUM, HIGH, or CRITICAL.
        labels: Tags for categorisation.

    Returns:
        API response envelope with the created issue data.
    """
    body: dict[str, Any] = {
        "title": title,
        "component_id": component_id,
        "description": description,
        "priority": priority,
        "labels": labels or [],
    }
    return _request("POST", "/api/v1/issues", body)


def get_issue(issue_id: str) -> dict:
    """Retrieve full details of a single issue by its ID."""
    return _request("GET", f"/api/v1/issues/{issue_id}")


def list_issues(
    status: str | None = None,
    component: str | None = None,
    page: int = 1,
    limit: int = 20,
) -> dict:
    """List issues with optional filters and pagination."""
    params: list[str] = []
    if status:
        params.append(f"status={status}")
    if component:
        params.append(f"component={component}")
    params.append(f"page={page}")
    params.append(f"limit={limit}")

    query = "&".join(params)
    return _request("GET", f"/api/v1/issues?{query}")


def close_issue(issue_id: str) -> dict:
    """Close an issue. Fails if it has open dependencies."""
    return _request("POST", f"/api/v1/issues/{issue_id}/close")


def update_issue(issue_id: str, updates: dict[str, Any]) -> dict:
    """Partially update an issue's fields."""
    return _request("PATCH", f"/api/v1/issues/{issue_id}", updates)


def delete_issue(issue_id: str) -> dict:
    """Permanently delete an issue and all its relationships."""
    return _request("DELETE", f"/api/v1/issues/{issue_id}")


def add_dependency(issue_id: str, depends_on_id: str) -> dict:
    """Create a DEPENDS_ON relationship between two issues."""
    body = {"depends_on_id": depends_on_id}
    return _request("POST", f"/api/v1/issues/{issue_id}/dependencies", body)


def remove_dependency(issue_id: str, depends_on_id: str) -> dict:
    """Remove a DEPENDS_ON relationship."""
    return _request("DELETE", f"/api/v1/issues/{issue_id}/dependencies/{depends_on_id}")


def get_dependencies(issue_id: str) -> dict:
    """List all issues that the given issue depends on."""
    return _request("GET", f"/api/v1/issues/{issue_id}/dependencies")


def get_dependents(issue_id: str) -> dict:
    """List all issues that depend on the given issue."""
    return _request("GET", f"/api/v1/issues/{issue_id}/dependents")


def get_dependency_chain(issue_id: str) -> dict:
    """Get the full transitive dependency chain for an issue."""
    return _request("GET", f"/api/v1/issues/{issue_id}/dependency-chain")


def get_blocked_issues() -> dict:
    """List all issues blocked by at least one open dependency."""
    return _request("GET", "/api/v1/blocked-issues")


def create_component(
    name: str,
    project: str,
    description: str | None = None,
) -> dict:
    """Create a new component to group issues."""
    body: dict[str, Any] = {
        "name": name,
        "project": project,
    }
    if description is not None:
        body["description"] = description
    return _request("POST", "/api/v1/components", body)


def list_components(project: str | None = None) -> dict:
    """List all components, optionally filtered by project."""
    query = f"?project={project}" if project else ""
    return _request("GET", f"/api/v1/components{query}")


def get_component(component_id: str) -> dict:
    """Retrieve full details of a single component."""
    return _request("GET", f"/api/v1/components/{component_id}")


def analyze_root_cause(
    test_id: str,
    test_name: str,
    error_message: str,
    component: str = "",
    labels: list[str] | None = None,
) -> dict:
    """Submit a test failure for root-cause analysis."""
    body: dict[str, Any] = {
        "test_id": test_id,
        "test_name": test_name,
        "error_message": error_message,
        "component": component,
        "labels": labels or [],
    }
    return _request("POST", "/api/v1/analyze/root-cause", body)


def analyze_impact(issue_id: str) -> dict:
    """Analyse what other issues and components would be affected."""
    return _request("GET", f"/api/v1/analyze/impact/{issue_id}")


def health_check() -> dict:
    """Check if the Tasker API is accessible and healthy."""
    return _request("GET", "/health")
