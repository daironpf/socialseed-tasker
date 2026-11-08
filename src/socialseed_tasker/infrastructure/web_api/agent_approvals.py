"""PostgreSQL-backed dependencies for human approval of agent actions (#616)."""

from __future__ import annotations

from socialseed_tasker.application.agent_approvals import AgentApprovalService
from socialseed_tasker.auth.agent_approval_store import PostgresAgentApprovalStore
from socialseed_tasker.config.storage import get_database_url


def create_agent_approval_store() -> PostgresAgentApprovalStore:
    """Create the persistence store used by the approval service."""
    database_url = get_database_url()
    if not database_url:
        raise RuntimeError("PostgreSQL not configured: TASKER_DATABASE_URL is not set")
    return PostgresAgentApprovalStore(database_url)


def create_agent_approval_service() -> AgentApprovalService:
    """Create a service whose store reloads state on every operation."""
    return AgentApprovalService(create_agent_approval_store())
