"""API route definitions orchestrator for issues, dependencies, components, and analysis.

Exposes all domain-specific routers from the routers subpackage.
Maintains full backward compatibility for app.py imports.
"""

from __future__ import annotations

# Import and expose all domain-specific routers
from socialseed_tasker.infrastructure.web_api.routers import (
    admin_router,
    agent_router,
    ai_search_router,
    analysis_router,
    auth_router,
    auto_healing_router,
    code_graph_router,
    commit_router,
    components_dep_router,
    components_router,
    constraints_router,
    cost_analytics_router,
    dependencies_router,
    epic_router,
    issues_router,
    label_router,
    objective_router,
    policy_rel_router,
    policy_router,
    project_router,
    rag_router,
    realtime_router,
    reasoning_router,
    secrets_router,
    sync_router,
    tenants_router,
    user_router,
    webhook_router,
)
from socialseed_tasker.infrastructure.web_api.routers import (
    chat_router as chat_router,
)
from socialseed_tasker.infrastructure.web_api.routers import (
    mcp_router as mcp_router,
)
from socialseed_tasker.infrastructure.web_api.routers.helpers import (
    construct_paginated_api_response as _paginated,
)
from socialseed_tasker.infrastructure.web_api.routers.helpers import (
    convert_domain_component_to_api_response as _component_to_response,
)
from socialseed_tasker.infrastructure.web_api.routers.helpers import (
    convert_domain_issue_to_api_response as _issue_to_response,
)
from socialseed_tasker.infrastructure.web_api.routers.helpers import (
    get_repository_provider as get_repo,
)
from socialseed_tasker.infrastructure.web_api.routers.helpers import (
    resolve_component_identifier_to_uuid as resolve_component_id,
)

# Maintain backward compatibility for any potential internal imports of helper dependencies
from socialseed_tasker.infrastructure.web_api.routers.helpers import (
    retrieve_neo4j_code_graph_driver as get_code_graph_driver,
)
