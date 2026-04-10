"""FastAPI application factory.

Creates the FastAPI app with metadata, CORS, routers, dependency injection,
custom OpenAPI schema for AI discovery, and global error handlers.
"""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from fastapi import FastAPI, HTTPException, Request, Response
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


@asynccontextmanager  # type: ignore[misc]
async def lifespan(app: FastAPI):
    """Application lifecycle hook.

    Runs startup/shutdown logic. Currently a placeholder for future
    Neo4j connection management.
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
            "A graph-based task management framework for AI agents.\n\n"
            "This API enables external AI agents to programmatically interact "
            "with the task management system. All endpoints return consistent "
            "JSON envelopes and support filtering, pagination, and discovery."
        ),
        version=__version__,
        license_info={
            "name": "Apache 2.0",
            "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
        },
        openapi_tags=[
            {
                "name": "issues",
                "description": "Create, read, update, delete, and close issues",
            },
            {
                "name": "dependencies",
                "description": "Manage [:DEPENDS_ON] relationships between issues",
            },
            {
                "name": "components",
                "description": "Manage project components that group issues",
            },
            {
                "name": "analysis",
                "description": "Root-cause analysis and impact assessment",
            },
            {
                "name": "health",
                "description": "System health and API discovery",
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

    # Register routers
    from socialseed_tasker.entrypoints.web_api.routes import (
        admin_router,
        agent_router,
        analysis_router,
        components_router,
        dependencies_router,
        issues_router,
        label_router,
        policy_router,
        project_router,
        sync_router,
        webhook_router,
    )

    app.include_router(issues_router, prefix="/api/v1", tags=["issues"])
    app.include_router(dependencies_router, prefix="/api/v1", tags=["dependencies"])
    app.include_router(components_router, prefix="/api/v1", tags=["components"])
    app.include_router(label_router, prefix="/api/v1", tags=["labels"])
    app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])
    app.include_router(project_router, prefix="/api/v1", tags=["projects"])
    app.include_router(policy_router, prefix="/api/v1", tags=["policies"])
    app.include_router(agent_router, prefix="/api/v1", tags=["agents"])
    app.include_router(sync_router, prefix="/api/v1", tags=["sync"])
    app.include_router(webhook_router, prefix="/api/v1", tags=["webhooks"])
    app.include_router(admin_router, prefix="/api/v1", tags=["admin"])

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
