"""Shared helper functions and FastAPI dependency providers for Web API routers.

Provides converters between domain entities and API response schemas,
repository dependency injectors, and ID resolution helpers.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from uuid import UUID

from fastapi import Depends, Request

from socialseed_tasker.core.task_management.actions import (
    ComponentNotFoundError,
    TaskRepositoryInterface,
)
from socialseed_tasker.core.task_management.entities import Component, Issue
from socialseed_tasker.entrypoints.web_api.schemas import (
    ComponentResponse,
    IssueResponse,
    Meta,
    PaginatedResponse,
    PaginationMeta,
)

logger = logging.getLogger(__name__)


def retrieve_neo4j_code_graph_driver(request: Request) -> Any:
    """Retrieve the raw Neo4j driver instance for code-graph endpoints.

    This acts as a dependency retriever that extracts the database connection
    driver directly from the FastAPI application's state.
    """
    if hasattr(request.app.state, "driver") and request.app.state.driver:
        database_driver_wrapper = request.app.state.driver
        if hasattr(database_driver_wrapper, "driver"):
            return database_driver_wrapper.driver
        return database_driver_wrapper
    return None


class RepositoryProviderDependency:
    """FastAPI dependency provider that injects the main TaskRepositoryInterface implementation from app state."""

    def __call__(self, request: Request) -> TaskRepositoryInterface:
        """Extract and return the repository from the application state."""
        return request.app.state.repository


# Shared instance of the repository provider dependency
get_repository_provider = RepositoryProviderDependency()


def resolve_component_identifier_to_uuid(
    partial_component_identifier: str,
    task_repository: TaskRepositoryInterface,
) -> UUID:
    """Resolve a partial component identifier (UUID prefix, full UUID, or exact name) to a full UUID.

    Args:
        partial_component_identifier: Full UUID string, partial UUID (4+ chars), or exact component name.
        task_repository: The task repository to perform lookups against.

    Returns:
        The resolved full UUID.

    Raises:
        ValueError: If the identifier format is invalid or cannot be resolved to any component.
    """
    # Try full UUID first
    try:
        return UUID(partial_component_identifier)
    except ValueError:
        pass

    # Minimum 4 characters for partial lookup OR exact name match
    if len(partial_component_identifier) < 4:
        raise ValueError(
            f"Invalid component ID format: {partial_component_identifier}. Need at least 4 characters."
        )

    # Try to find by exact name match first (names can be short)
    try:
        matched_component = task_repository.get_component_by_name(partial_component_identifier)
        if matched_component:
            return matched_component.id
    except Exception:
        pass

    # Search for matching component by prefix (UUID-like patterns need 8+)
    if len(partial_component_identifier) >= 8:
        all_components = task_repository.list_components()
        for component in all_components:
            if str(component.id).startswith(partial_component_identifier):
                return component.id

    raise ValueError(f"Component not found: {partial_component_identifier}")


def convert_domain_issue_to_api_response(domain_issue: Issue) -> IssueResponse:
    """Convert a domain Issue entity into a standardized API IssueResponse schema.

    Enforces self-documenting property mappings.
    """
    return IssueResponse(
        id=str(domain_issue.id),
        title=domain_issue.title,
        description=domain_issue.description,
        status=domain_issue.status.value,
        priority=domain_issue.priority.value,
        component_id=str(domain_issue.component_id),
        labels=domain_issue.labels,
        dependencies=[str(dep_id) for dep_id in domain_issue.dependencies],
        blocks=[str(blocked_id) for blocked_id in domain_issue.blocks],
        affects=[str(affected_id) for affected_id in domain_issue.affects],
        created_at=domain_issue.created_at,
        updated_at=domain_issue.updated_at,
        closed_at=domain_issue.closed_at,
        architectural_constraints=domain_issue.architectural_constraints,
        agent_working=domain_issue.agent_working,
        reasoning_logs=[
            {
                "id": str(log.id),
                "timestamp": log.timestamp,
                "context": log.context.value,
                "reasoning": log.reasoning,
                "related_nodes": [str(node_id) for node_id in log.related_nodes],
            }
            for log in domain_issue.reasoning_logs
        ],
        manifest_todo=domain_issue.manifest_todo,
        manifest_files=domain_issue.manifest_files,
        manifest_notes=domain_issue.manifest_notes,
        agent_started_at=domain_issue.agent_started_at,
        agent_finished_at=domain_issue.agent_finished_at,
        agent_id=domain_issue.agent_id,
    )


def convert_domain_component_to_api_response(domain_component: Component) -> ComponentResponse:
    """Convert a domain Component entity into a standardized API ComponentResponse schema."""
    return ComponentResponse(
        id=str(domain_component.id),
        name=domain_component.name,
        description=domain_component.description,
        project=domain_component.project,
        created_at=domain_component.created_at,
        updated_at=domain_component.updated_at,
    )


def construct_paginated_api_response(
    paginated_items: list[Any],
    current_page: int,
    items_per_page: int,
    total_items_count: int,
) -> PaginatedResponse[Any]:
    """Construct a standardized paginated response wrapping the given items list."""
    return PaginatedResponse(
        items=paginated_items,
        pagination=PaginationMeta(
            page=current_page,
            limit=items_per_page,
            total=total_items_count,
            has_next=(current_page * items_per_page) < total_items_count,
            has_prev=current_page > 1,
        ),
    )
