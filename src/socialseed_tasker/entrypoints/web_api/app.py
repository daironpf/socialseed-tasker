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

from socialseed_tasker.core.task_management.actions import (
    CircularDependencyError,
    ComponentNotFoundError,
    IssueAlreadyClosedError,
    IssueNotFoundError,
    OpenDependenciesError,
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
        version="0.5.0",
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

    @app.middleware("http")
    async def api_key_auth_middleware(request: Request, call_next):
        if api_key is None:
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

    # Register routers
    from socialseed_tasker.entrypoints.web_api.routes import (
        admin_router,
        analysis_router,
        components_router,
        dependencies_router,
        issues_router,
        project_router,
    )

    app.include_router(issues_router, prefix="/api/v1", tags=["issues"])
    app.include_router(dependencies_router, prefix="/api/v1", tags=["dependencies"])
    app.include_router(components_router, prefix="/api/v1", tags=["components"])
    app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])
    app.include_router(project_router, prefix="/api/v1", tags=["projects"])
    app.include_router(admin_router, prefix="/api/v1", tags=["admin"])

    # Health endpoint with Neo4j connectivity check
    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, Any]:
        result = {"status": "healthy", "version": "0.5.0"}

        if neo4j_driver is not None:
            neo4j_connected = neo4j_driver.health_check()
            result["neo4j"] = "connected" if neo4j_connected else "disconnected"
            result["neo4j_uri"] = neo4j_driver.uri
            if not neo4j_connected:
                result["status"] = "degraded"

        return result

    # Dependency injection - provide repository to all routes
    app.state.repository = repository

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
