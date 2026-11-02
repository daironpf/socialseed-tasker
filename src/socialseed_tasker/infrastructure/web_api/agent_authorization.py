"""PostgreSQL-backed agent authorization dependencies."""

from __future__ import annotations

from socialseed_tasker.application.agent_authorization import AgentActionAuthorizer
from socialseed_tasker.auth.user_store import (
    TOOLS_SEED,
    PostgresAgentPermissionPolicyStore,
    PostgresAgentProfileStore,
)
from socialseed_tasker.config.storage import get_database_url
from socialseed_tasker.domain.entities import Component


def create_agent_action_authorizer() -> AgentActionAuthorizer:
    """Create an authorizer whose stores reload state on every decision."""
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("PostgreSQL not configured: TASKER_DATABASE_URL is not set")
    return AgentActionAuthorizer(
        PostgresAgentProfileStore(database_url),
        PostgresAgentPermissionPolicyStore(database_url),
        [slug for slug, _, _ in TOOLS_SEED],
    )


def create_agent_profile_store() -> PostgresAgentProfileStore:
    """Create the profile/run store used to validate execution credentials."""
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("PostgreSQL not configured: TASKER_DATABASE_URL is not set")
    return PostgresAgentProfileStore(database_url)


def resolve_component_project_id(component: Component, repository: object) -> str | None:
    """Resolve the component's project against backend Project nodes only."""
    project_reader = getattr(repository, "list_project_nodes", None)
    if not callable(project_reader):
        return str(component.project_id) if component.project_id else None

    nodes = project_reader()
    if nodes is None:
        return str(component.project_id) if component.project_id else None
    matches = [
        node
        for node in nodes
        if str(component.project) in {
            str(node.get("id") or ""),
            str(node.get("name") or ""),
            str(node.get("slug") or ""),
        }
    ]
    if component.project_id:
        matches = [
            node for node in matches if str(node.get("id") or "") == str(component.project_id)
        ]
    if len(matches) != 1 or not matches[0].get("id"):
        return None
    return str(matches[0]["id"])
