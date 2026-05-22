"""FastAPI-based REST implementation."""

from socialseed_tasker.entrypoints.web_api.routes import (
    admin_router,
    agent_router,
    analysis_router,
    components_dep_router,
    components_router,
    constraints_router,
    dependencies_router,
    epic_router,
    label_router,
    objective_router,
    policy_router,
    project_router,
    sync_router,
    webhook_router,
)
