"""FastAPI application factory.

Creates the FastAPI app with metadata, CORS, routers, dependency injection,
custom OpenAPI schema for AI discovery, and global error handlers.
Includes performance monitoring middleware and Neo4j index management.
"""

from __future__ import annotations

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from functools import lru_cache
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from socialseed_tasker import __version__  # noqa: E402
from socialseed_tasker.core.task_management.actions import (
    CircularDependencyError,
    ComponentNotFoundError,
    IssueAlreadyClosedError,
    IssueNotFoundError,
    OpenDependenciesError,
    PolicyViolationError,
)

if TYPE_CHECKING:
    from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
    from socialseed_tasker.storage.graph_database.driver import Neo4jDriver

logger = logging.getLogger(__name__)

SLOW_REQUEST_THRESHOLD = float(os.getenv("TASKER_SLOW_REQUEST_THRESHOLD", "0.5"))
ENABLE_PERF_LOGGING = os.getenv("TASKER_ENABLE_PERF_LOGGING", "true").lower() == "true"


@lru_cache(maxsize=128)
def _get_performance_targets() -> dict[str, float]:
    """Cached performance targets in milliseconds."""
    return {
        "GET /api/v1/issues": 100,
        "GET /api/v1/issues/{id}": 50,
        "POST /api/v1/analyze/impact": 500,
        "GET /api/v1/graph/dependencies": 200,
    }


@asynccontextmanager  # type: ignore[misc]
async def lifespan(app: FastAPI):
    """Application lifecycle hook.

    Runs startup/shutdown logic. Initializes Neo4j indexes and handles
    connection management.
    """
    yield


def create_app(
    repository: TaskRepositoryInterface | None = None,
    neo4j_driver: Neo4jDriver | None = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    Intent: Assemble all API components into a single application instance.
    Business Value: Factory pattern enables testing with mock repositories
    and different configurations.
    """
    app = FastAPI(
        title="SocialSeed Tasker API",
        description=(
            "## A Graph-Based Task Management Framework for AI Agents\n\n"
            "SocialSeed Tasker uses Neo4j as its exclusive source of truth, "
            "modeling issues, components, and dependencies as a directed graph.\n\n"
            "### Key Features\n"
            "- **Graph-Native**: All data modeled as nodes and relationships\n"
            "- **AI-Ready**: OpenAPI spec designed for AI agent consumption\n"
            "- **Consistent Envelopes**: All responses use `{data, error, meta}` format\n"
            "- **Pagination**: List endpoints support page/limit pagination\n"
            "- **Filtering**: Filter by status, component, project, and labels\n\n"
            "### Authentication\n"
            "Set `X-API-Key` header or `Authorization: Bearer <token>` for authenticated requests.\n"
            "Enable with `TASKER_AUTH_ENABLED=true`.\n\n"
            "### OpenAPI Discovery\n"
            "- Swagger UI: `/docs`\n"
            "- ReDoc: `/redoc`\n"
            "- OpenAPI JSON: `/openapi.json`"
        ),
        version=__version__,
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
        openapi_tags=[
            {
                "name": "issues",
                "description": "Create, read, update, delete, and close issues. "
                "All issues belong to a component and can have dependencies.",
            },
            {
                "name": "dependencies",
                "description": "Manage [:DEPENDS_ON] relationships between issues. "
                "Prevents circular dependencies and tracks blocked issues.",
            },
            {
                "name": "components",
                "description": "Manage project components that group issues. "
                "Components represent architectural layers or functional areas.",
            },
            {
                "name": "analysis",
                "description": "Root-cause analysis and impact assessment using graph proximity. "
                "Links test failures to closed issues and calculates risk levels.",
            },
            {
                "name": "health",
                "description": "System health checks and API discovery. "
                "Returns Neo4j connectivity status.",
            },
            {
                "name": "projects",
                "description": "Project-level operations and summaries. "
                "Filter and aggregate data by project name.",
            },
            {
                "name": "agents",
                "description": "AI agent lifecycle management. "
                "Track agent work status, start/finish timestamps, and reasoning logs.",
            },
            {
                "name": "deployments",
                "description": "Deployment traceability. "
                "Track which issues are deployed to which environments (PROD, STAGING, DEV).",
            },
        ],
        lifespan=lifespan,
    )

    # CORS for browser access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API Key authentication
    api_key = os.getenv("TASKER_API_KEY")
    auth_enabled = os.getenv("TASKER_AUTH_ENABLED", "false").lower() == "true"

    @app.middleware("http")
    async def api_key_auth_middleware(request: Request, call_next):
        # Skip auth if no API key configured or auth disabled in development
        if api_key is None or not auth_enabled:
            return await call_next(request)

        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        provided_key = request.headers.get("X-API-Key")
        if provided_key is None:
            auth_header = request.headers.get("Authorization", "")
            if auth_header.startswith("Bearer "):
                provided_key = auth_header[7:]
        if provided_key != api_key:
            return JSONResponse(
                status_code=401,
                content={"error": {"code": "UNAUTHORIZED", "message": "Invalid or missing API key"}},
            )

        return await call_next(request)

    # Rate limiting
    rate_limit_enabled = os.getenv("TASKER_RATE_LIMIT_ENABLED", "false").lower() == "true"
    rate_limit_per_minute = int(os.getenv("TASKER_RATE_LIMIT_PER_MINUTE", "100"))
    rate_limit_per_hour = int(os.getenv("TASKER_RATE_LIMIT_PER_HOUR", "1000"))

    _rate_limit_store: dict[str, list[float]] = {}

    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        from time import time

        if not rate_limit_enabled:
            return await call_next(request)

        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time()
        window_start = now - 60

        if client_ip not in _rate_limit_store:
            _rate_limit_store[client_ip] = []

        _rate_limit_store[client_ip] = [ts for ts in _rate_limit_store[client_ip] if ts > window_start]

        if len(_rate_limit_store[client_ip]) >= rate_limit_per_minute:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Rate limit exceeded. Try again later.",
                        "details": {
                            "limit": rate_limit_per_minute,
                            "remaining": 0,
                            "reset": int(window_start + 60),
                        },
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(rate_limit_per_minute),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(window_start + 60)),
                },
            )

        _rate_limit_store[client_ip].append(now)

        remaining = rate_limit_per_minute - len(_rate_limit_store[client_ip])
        reset_time = int(window_start + 60)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(rate_limit_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_time)

        return response

    # Performance monitoring middleware
    @app.middleware("http")
    async def performance_monitoring_middleware(request: Request, call_next):
        if not ENABLE_PERF_LOGGING:
            return await call_next(request)

        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # Add timing header
        response.headers["X-Response-Time-Ms"] = f"{duration_ms:.2f}"

        # Log slow requests
        if duration_ms > SLOW_REQUEST_THRESHOLD * 1000:
            logger.warning(
                f"Slow request: {request.method} {request.url.path} "
                f"took {duration_ms:.2f}ms (threshold: {SLOW_REQUEST_THRESHOLD * 1000:.2f}ms)"
            )

        return response

    # Register routers
    # Register routers
    from socialseed_tasker.entrypoints.web_api.routes import (
        admin_router,
        agent_router,
        ai_search_router,
        analysis_router,
        code_graph_router,
        components_dep_router,
        components_router,
        constraints_router,
        cost_analytics_router,
        dependencies_router,
        epic_router,
        issues_router,
        label_router,
        objective_router,
        policy_router,
        project_router,
        sync_router,
        webhook_router,
    )

    app.include_router(issues_router, prefix="/api/v1", tags=["issues"])
    app.include_router(dependencies_router, prefix="/api/v1", tags=["dependencies"])
    app.include_router(components_router, prefix="/api/v1", tags=["components"])
    app.include_router(components_dep_router, prefix="/api/v1", tags=["components"])
    app.include_router(constraints_router, prefix="/api/v1", tags=["constraints"])
    app.include_router(label_router, prefix="/api/v1", tags=["labels"])
    app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])
    app.include_router(project_router, prefix="/api/v1", tags=["projects"])
    app.include_router(policy_router, prefix="/api/v1", tags=["policies"])
    app.include_router(agent_router, prefix="/api/v1", tags=["agents"])
    app.include_router(sync_router, prefix="/api/v1", tags=["sync"])
    app.include_router(webhook_router, prefix="/api/v1", tags=["webhooks"])
    app.include_router(admin_router, prefix="/api/v1", tags=["admin"])
    app.include_router(epic_router, prefix="/api/v1", tags=["epics"])
    app.include_router(objective_router, prefix="/api/v1", tags=["objectives"])
    app.include_router(cost_analytics_router, prefix="/api/v1", tags=["cost_analytics"])
    app.include_router(ai_search_router, prefix="/api/v1/ai", tags=["ai_search"])
    app.include_router(code_graph_router, prefix="/api/v1/code-graph", tags=["code-graph"])

    # Health endpoint with Neo4j connectivity check
    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, Any]:
        result = {
            "status": "healthy",
            "version": __version__,
            "authentication": {
                "enabled": auth_enabled,
                "configured": api_key is not None,
            },
            "rate_limiting": {
                "enabled": rate_limit_enabled,
                "per_minute": rate_limit_per_minute,
                "per_hour": rate_limit_per_hour,
            },
        }

        if neo4j_driver is not None:
            neo4j_connected = neo4j_driver.health_check()
            result["neo4j"] = "connected" if neo4j_connected else "disconnected"
            result["neo4j_uri"] = neo4j_driver.uri
            if not neo4j_connected:
                result["status"] = "degraded"

        try:
            import json
            from pathlib import Path

            project_json_path = Path(__file__).parent.parent.parent / "assets" / "templates" / "tasker" / "project.json"
            if project_json_path.exists():
                result["project_config"] = json.loads(project_json_path.read_text(encoding="utf-8"))
        except Exception:
            pass

        try:
            import httpx

            result["httpx"] = "available"
        except ImportError:
            result["httpx"] = "not installed"

        return result

    # Dependency injection - provide repository to all routes
    app.state.repository = repository

    # Provide config to routes for policy enforcement mode
    if hasattr(repository, "_driver") and hasattr(repository._driver, "_config"):
        app.state.config = repository._driver._config
    else:
        from socialseed_tasker.bootstrap.container import AppConfig

        app.state.config = AppConfig()

    # Global exception handlers
    @app.exception_handler(IssueNotFoundError)
    async def issue_not_found_handler(request: Request, exc: IssueNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=_error_response("ISSUE_NOT_FOUND", str(exc)),
        )

    @app.exception_handler(ComponentNotFoundError)
    async def component_not_found_handler(request: Request, exc: ComponentNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content=_error_response("COMPONENT_NOT_FOUND", str(exc)),
        )

    @app.exception_handler(CircularDependencyError)
    async def circular_dependency_handler(request: Request, exc: CircularDependencyError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=_error_response("CIRCULAR_DEPENDENCY", str(exc)),
        )

    @app.exception_handler(PolicyViolationError)
    async def policy_violation_handler(request: Request, exc: PolicyViolationError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "POLICY_VIOLATION",
                    "message": f"Operation blocked by policy '{exc.policy_name}'",
                    "details": {
                        "policy": exc.policy_name,
                        "rule_type": exc.rule_type,
                        "message": exc.message,
                        "suggestion": exc.suggestion,
                    },
                },
            },
        )

    @app.exception_handler(IssueAlreadyClosedError)
    async def issue_already_closed_handler(request: Request, exc: IssueAlreadyClosedError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=_error_response("ISSUE_ALREADY_CLOSED", str(exc)),
        )

    @app.exception_handler(OpenDependenciesError)
    async def open_dependencies_handler(request: Request, exc: OpenDependenciesError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content=_error_response("OPEN_DEPENDENCIES", str(exc)),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=_error_response("VALIDATION_ERROR", str(exc)),
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content=_error_response(
                "INTERNAL_ERROR",
                "An unexpected error occurred",
                {"detail": str(exc) if app.debug else None},
            ),
        )

    return app


def _error_response(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build a consistent error response envelope."""
    return {
        "data": None,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "meta": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": str(uuid.uuid4()),
        },
    }
