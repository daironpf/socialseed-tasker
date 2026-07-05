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
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request as StarletteRequest

from socialseed_tasker import __version__  # noqa: E402
from socialseed_tasker.observability.tracing import init_tracing, get_tracer
from socialseed_tasker.application.actions import (
    CircularDependencyError,
    ComponentNotFoundError,
    IssueAlreadyClosedError,
    IssueNotFoundError,
    OpenDependenciesError,
    PolicyViolationError,
)
from socialseed_tasker.application.exceptions import GraphPortError

if TYPE_CHECKING:
    from socialseed_tasker.application.actions import TaskRepositoryInterface
    from socialseed_tasker.infrastructure.neo4j_driver import Neo4jDriver

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

    # initialize tracing for API
    try:
        init_tracing(app=app, service_name=os.getenv("TASKER_OTEL_SERVICE", "tasker-api"))
    except Exception:
        pass
    tracer = get_tracer("tasker.api")

    # CORS for browser access — configurable via TASKER_API_ALLOW_ORIGINS (comma separated)
    allow_origins_env = os.getenv("TASKER_API_ALLOW_ORIGINS", "http://localhost:8080")
    allow_origins = [o.strip() for o in allow_origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
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
            retry_after = int(window_start + 60 - now)
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
                    "Retry-After": str(retry_after),
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

    # Reasoning Capture Middleware
    @app.middleware("http")
    async def reasoning_capture_middleware(request: Request, call_next):
        response = await call_next(request)
        
        reasoning_header = request.headers.get("X-Agent-Reasoning")
        if reasoning_header and "api/v1/issues/" in request.url.path:
            parts = request.url.path.split("/")
            try:
                issue_idx = parts.index("issues")
                if len(parts) > issue_idx + 1:
                    issue_id = parts[issue_idx + 1]
                    import uuid
                    try:
                        uuid.UUID(issue_id)
                        
                        from socialseed_tasker.infrastructure.neo4j_reasoning_repository import ReasoningRepository
                        from socialseed_tasker.domain.entities import ReasoningNode, DecisionType
                        import json
                        
                        driver = getattr(app.state, "driver", None)
                        if driver:
                            repo = ReasoningRepository(driver)
                            try:
                                data = json.loads(reasoning_header)
                                thought = data.get("thought", str(reasoning_header))
                                confidence = float(data.get("confidence", 0.8))
                                alternatives = data.get("alternatives_considered", [])
                                decision = data.get("decision", "action_execution")
                                decision_type = DecisionType.UNKNOWN
                                try:
                                    if "decision_type" in data:
                                        decision_type = DecisionType(data["decision_type"])
                                except ValueError:
                                    pass
                                    
                                node = ReasoningNode(
                                    thought=thought,
                                    confidence=confidence,
                                    alternatives_considered=alternatives,
                                    decision=decision,
                                    decision_type=decision_type
                                )
                                agent_id = request.headers.get("X-Agent-ID", "unknown-agent")
                                agent_name = request.headers.get("X-Agent-Name", "Unknown Agent")
                                repo.log_reasoning(issue_id, agent_id, agent_name, node)
                            except json.JSONDecodeError:
                                node = ReasoningNode(thought=reasoning_header, confidence=0.5, decision="action_execution")
                                agent_id = request.headers.get("X-Agent-ID", "unknown-agent")
                                agent_name = request.headers.get("X-Agent-Name", "Unknown Agent")
                                repo.log_reasoning(issue_id, agent_id, agent_name, node)
                    except ValueError:
                        pass
            except Exception as e:
                logger.error(f"Failed to capture reasoning: {e}")
                
        return response

    # Health endpoint with Neo4j check is registered below with the routers
    # Register routers
    # Register routers
    from socialseed_tasker.infrastructure.web_api.routes import (
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
        policy_rel_router,
        project_router,
        rag_router,
        reasoning_router,
        sync_router,
        tenants_router,
        user_router,
        commit_router,
        webhook_router,
        secrets_router,
    )
    from socialseed_tasker.events.routes import webhook_router as events_webhook_router

    app.include_router(issues_router, prefix="/api/v1", tags=["issues"])
    app.include_router(dependencies_router, prefix="/api/v1", tags=["dependencies"])
    app.include_router(components_router, prefix="/api/v1", tags=["components"])
    app.include_router(components_dep_router, prefix="/api/v1", tags=["components"])
    app.include_router(constraints_router, prefix="/api/v1", tags=["constraints"])
    app.include_router(label_router, prefix="/api/v1", tags=["labels"])
    app.include_router(analysis_router, prefix="/api/v1", tags=["analysis"])
    app.include_router(project_router, prefix="/api/v1", tags=["projects"])
    app.include_router(policy_router, prefix="/api/v1", tags=["policies"])
    app.include_router(policy_rel_router, prefix="/api/v1", tags=["policy-relationships"])
    app.include_router(agent_router, prefix="/api/v1", tags=["agents"])
    app.include_router(sync_router, prefix="/api/v1", tags=["sync"])
    app.include_router(webhook_router, prefix="/api/v1", tags=["webhooks"])
    app.include_router(admin_router, prefix="/api/v1", tags=["admin"])
    app.include_router(epic_router, prefix="/api/v1", tags=["epics"])
    app.include_router(objective_router, prefix="/api/v1", tags=["objectives"])
    app.include_router(cost_analytics_router, prefix="/api/v1", tags=["cost_analytics"])
    app.include_router(ai_search_router, prefix="/api/v1/ai", tags=["ai_search"])
    app.include_router(code_graph_router, prefix="/api/v1/code-graph", tags=["code-graph"])
    app.include_router(rag_router, prefix="/api/v1", tags=["rag"])
    app.include_router(reasoning_router, prefix="/api/v1", tags=["reasoning"])
    app.include_router(user_router, prefix="/api/v1", tags=["users"])
    app.include_router(commit_router, prefix="/api/v1", tags=["commits"])
    app.include_router(secrets_router, prefix="", tags=["secrets"])
    app.include_router(tenants_router, prefix="/api/v1", tags=["tenants"])
    app.include_router(events_webhook_router, tags=["webhooks"])

    from socialseed_tasker.data_catalog.api import router as registry_router
    app.include_router(registry_router)

    from socialseed_tasker.data_quality.api import router as data_quality_router
    app.include_router(data_quality_router)

    from socialseed_tasker.graphviz.server import router as graphviz_router
    app.include_router(graphviz_router)

    # Health endpoint with Neo4j connectivity check
    @app.get("/health", tags=["health"])
    def health_check() -> dict[str, Any]:
        import sys

        result: dict[str, Any] = {
            "status": "healthy",
            "version": __version__,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "authentication": {
                "enabled": auth_enabled,
                "configured": api_key is not None,
            },
            "rate_limiting": {
                "enabled": rate_limit_enabled,
                "burst": 20,
                "per_minute": rate_limit_per_minute,
                "per_hour": rate_limit_per_hour,
                "docs": "https://github.com/anomalyco/socialseed-tasker",
            },
            "dependencies": {},
        }

        if neo4j_driver is not None:
            neo4j_connected = neo4j_driver.health_check()
            result["dependencies"]["neo4j"] = "connected" if neo4j_connected else "disconnected"
            from urllib.parse import urlparse
            parsed = urlparse(neo4j_driver.uri)
            result["neo4j_uri"] = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}" if parsed.hostname else neo4j_driver.uri
            if not neo4j_connected:
                result["status"] = "degraded"
        else:
            result["dependencies"]["neo4j"] = "not configured"

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

            result["dependencies"]["httpx"] = "available"
        except ImportError:
            result["dependencies"]["httpx"] = "not installed"

        return result

    # Dependency injection - provide repository and driver to all routes
    app.state.repository = repository
    app.state.driver = neo4j_driver

    # Events wiring
    from socialseed_tasker.infrastructure.memory_storage import MemoryStorage
    from socialseed_tasker.events.webhooks import WebhookManager
    from socialseed_tasker.events.bus import EventBus
    from socialseed_tasker.events.delivery import DeliveryWorker
    evt_storage = MemoryStorage()
    app.state.events = WebhookManager(storage=evt_storage)
    app.state.events_bus = EventBus()
    app.state.delivery_worker = DeliveryWorker(storage=evt_storage)
    if os.getenv("TASKER_INTEGRATION") == "1":
        app.state.delivery_worker.start()

    # SSO / Keycloak wiring
    from socialseed_tasker.auth.oauth import SessionStore
    app.state.session_store = SessionStore(storage=evt_storage)

    from fastapi.responses import RedirectResponse
    import secrets
    import urllib.parse as urlparse

    @app.get("/auth/login")
    def auth_login(request: Request):
        base = os.getenv("TASKER_BASE_URL", "http://localhost:8000")
        state = secrets.token_urlsafe(16)
        from socialseed_tasker.auth.oauth import start_login_redirect
        url = start_login_redirect(base, state)
        return RedirectResponse(url)

    @app.get("/auth/callback")
    def auth_callback(code: str | None = None, request: Request = None):
        if not code:
            return JSONResponse(status_code=400, content={"status": "error", "error": "missing code"})
        base = os.getenv("TASKER_BASE_URL", "http://localhost:8000")
        session_store = app.state.session_store
        from socialseed_tasker.auth.oauth import handle_oauth_callback, SESSION_COOKIE_NAME
        try:
            info = handle_oauth_callback(code, base, session_store)
            sid = info["sid"]
            response = JSONResponse(content={"status": "ok"})
            response.set_cookie(SESSION_COOKIE_NAME, sid, httponly=True, secure=False, max_age=int(os.getenv("TASKER_SESSION_TTL", "3600")))
            return response
        except Exception as exc:
            return JSONResponse(status_code=500, content={"status": "error", "error": str(exc)})

    @app.post("/auth/logout")
    def auth_logout(request: Request):
        from socialseed_tasker.auth.oauth import SESSION_COOKIE_NAME, _logout_endpoint
        sid = request.cookies.get(SESSION_COOKIE_NAME)
        if sid:
            app.state.session_store.delete(sid)
        logout_url = _logout_endpoint() + "?redirect_uri=" + urlparse.quote(os.getenv("TASKER_BASE_URL", "http://localhost:8000"))
        resp = RedirectResponse(logout_url)
        resp.delete_cookie(SESSION_COOKIE_NAME)
        return resp

    @app.get("/api/v1/whoami")
    def whoami(request: Request):
        from socialseed_tasker.auth.oauth import SESSION_COOKIE_NAME
        sid = request.cookies.get(SESSION_COOKIE_NAME)
        if sid:
            session = app.state.session_store.get(sid)
            if session:
                claims = session.get("claims", {})
                username = claims.get("preferred_username") or claims.get("sub")
                return {"username": username, "authenticated": True}
        auth = request.headers.get("authorization")
        if auth and auth.lower().startswith("bearer "):
            token = auth.split(" ", 1)[1]
            from socialseed_tasker.auth.auth import load_auth_provider
            provider = load_auth_provider()
            user_id = provider.verify_token(token)
            if user_id:
                return {"username": user_id, "authenticated": True}
        return {"username": None, "authenticated": False}

    if os.getenv("TASKER_INTEGRATION") == "1":
        @app.post("/test/create_session")
        async def test_create_session(request: Request):
            from socialseed_tasker.auth.oauth import SESSION_COOKIE_NAME, parse_id_token
            import json as _json
            raw = await request.body()
            body = _json.loads(raw.decode("utf-8")) if raw else {}
            id_token = body.get("id_token", "")
            access_token = body.get("access_token", "")
            refresh_token = body.get("refresh_token", "")
            claims = parse_id_token(id_token) if id_token else {}
            session = {
                "id_token": id_token,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "claims": claims,
                "created_at": __import__("time").time(),
            }
            sid = app.state.session_store.create(session)
            response = JSONResponse(content={"status": "ok", "sid": sid})
            response.set_cookie(SESSION_COOKIE_NAME, sid, httponly=True, secure=False, max_age=3600)
            return response

    # Rate limiter wiring
    from socialseed_tasker.infrastructure.memory_rate_limiter import MemoryRateLimiter
    try:
        from socialseed_tasker.infrastructure.redis_rate_limiter import RedisRateLimiter
        _REDIS_AVAILABLE = True
    except Exception:
        _REDIS_AVAILABLE = False
    _rate_redis_url = os.getenv("TASKER_REDIS_URL")
    if _rate_redis_url and _REDIS_AVAILABLE:
        try:
            app.state.rate_limiter = RedisRateLimiter(_rate_redis_url)
        except Exception:
            app.state.rate_limiter = MemoryRateLimiter()
    else:
        app.state.rate_limiter = MemoryRateLimiter()
    # Register rate-limit middleware
    from socialseed_tasker.infrastructure.web_api.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)

    # Tenant middleware
    from socialseed_tasker.tenancy.middleware import TenantMiddleware
    from socialseed_tasker.cli.wiring import build_default_container
    _tenancy_container = build_default_container()
    app.add_middleware(TenantMiddleware, container=_tenancy_container)

    # Admin rate-limit endpoints
    def _require_rate_access(request: Request):
        if not auth_enabled:
            return True
        from socialseed_tasker.auth.auth import load_auth_provider
        auth = request.headers.get("authorization", "")
        user_id = None
        if auth.lower().startswith("bearer "):
            user_id = load_auth_provider().verify_token(auth.split(" ", 1)[1])
        if not user_id:
            sid = request.cookies.get(os.getenv("TASKER_SESSION_COOKIE", "TASKER_SESSION"))
            if sid:
                session_store = getattr(app.state, "session_store", None)
                if session_store:
                    session = session_store.get(sid)
                    if session:
                        claims = session.get("claims", {})
                        user_id = claims.get("preferred_username") or claims.get("sub")
        return user_id is not None

    @app.get("/api/v1/admin/rate/{key}")
    def admin_get_rate(key: str, request: Request):
        from fastapi import HTTPException
        if not _require_rate_access(request) or not getattr(app.state, "rate_limiter", None):
            raise HTTPException(status_code=403, detail="forbidden")
        state = app.state.rate_limiter.get_state(key)
        return {"status": "ok", "key": key, "state": state}

    @app.post("/api/v1/admin/rate/{key}/reset")
    def admin_reset_rate(key: str, request: Request):
        from fastapi import HTTPException
        if not _require_rate_access(request) or not getattr(app.state, "rate_limiter", None):
            raise HTTPException(status_code=403, detail="forbidden")
        app.state.rate_limiter.reset(key)
        return {"status": "ok", "key": key}

    # Admin helpers
    def _require_admin(request: Request):
        if not auth_enabled:
            return None
        from socialseed_tasker.auth.auth import load_auth_provider
        from socialseed_tasker.cli.wiring import build_default_container
        auth = request.headers.get("authorization", "")
        user_id = None
        if auth.lower().startswith("bearer "):
            user_id = load_auth_provider().verify_token(auth.split(" ", 1)[1])
        if not user_id:
            raise HTTPException(status_code=403, detail="forbidden")
        container = build_default_container()
        if not container.rbac.has_permission(user_id, "admin"):
            raise HTTPException(status_code=403, detail="forbidden")
        return container

    # Admin feature-flag endpoints
    @app.get("/api/v1/admin/flags")
    def api_list_flags(request: Request):
        from fastapi import HTTPException
        container = _require_admin(request)
        if container is None:
            from socialseed_tasker.cli.wiring import build_default_container
            container = build_default_container()
        return {"status": "ok", "flags": container.runtime_config.list()}

    @app.get("/api/v1/admin/flags/{name}")
    def api_get_flag(name: str, request: Request):
        from fastapi import HTTPException
        container = _require_admin(request)
        if container is None:
            from socialseed_tasker.cli.wiring import build_default_container
            container = build_default_container()
        v = container.runtime_config.get(name, None)
        if v is None:
            raise HTTPException(status_code=404, detail="not found")
        return {"status": "ok", "name": name, "value": v}

    @app.post("/api/v1/admin/flags")
    async def api_set_flag(request: Request):
        from fastapi import HTTPException
        import json as _json
        container = _require_admin(request)
        if container is None:
            from socialseed_tasker.cli.wiring import build_default_container
            container = build_default_container()
        raw = await request.body()
        body = _json.loads(raw.decode("utf-8")) if raw else {}
        name = body.get("name")
        value = body.get("value")
        if not name:
            raise HTTPException(status_code=400, detail="missing name")
        container.runtime_config.set(name, value)
        return {"status": "ok", "name": name, "value": value}

    @app.delete("/api/v1/admin/flags/{name}")
    def api_delete_flag(name: str, request: Request):
        from fastapi import HTTPException
        container = _require_admin(request)
        if container is None:
            from socialseed_tasker.cli.wiring import build_default_container
            container = build_default_container()
        container.runtime_config.delete(name)
        return {"status": "ok", "name": name}

    # Privacy / GDPR endpoints
    @app.post("/api/v1/privacy/export")
    async def api_privacy_export(request: Request):
        from fastapi import HTTPException
        from socialseed_tasker.auth.auth import load_auth_provider
        from socialseed_tasker.cli.wiring import build_default_container
        import json as _json
        auth = request.headers.get("authorization", "")
        user_id = None
        if auth.lower().startswith("bearer "):
            user_id = load_auth_provider().verify_token(auth.split(" ", 1)[1])
        if not user_id:
            raise HTTPException(status_code=403, detail="forbidden")
        raw = await request.body()
        body = _json.loads(raw.decode("utf-8")) if raw else {}
        subject = body.get("subject_id")
        if not subject:
            raise HTTPException(status_code=400, detail="missing subject_id")
        container = build_default_container()
        if user_id != subject and not container.rbac.has_permission(user_id, "admin"):
            raise HTTPException(status_code=403, detail="forbidden")
        path = container.privacy_handlers.export_subject(subject, container)
        return {"status": "ok", "export_path": path}

    @app.post("/api/v1/privacy/delete")
    async def api_privacy_delete(request: Request):
        from fastapi import HTTPException
        from socialseed_tasker.auth.auth import load_auth_provider
        from socialseed_tasker.cli.wiring import build_default_container
        import json as _json
        import time
        auth = request.headers.get("authorization", "")
        user_id = None
        if auth.lower().startswith("bearer "):
            user_id = load_auth_provider().verify_token(auth.split(" ", 1)[1])
        if not user_id:
            raise HTTPException(status_code=403, detail="forbidden")
        raw_body = await request.body()
        body = _json.loads(raw_body.decode("utf-8")) if raw_body else {}
        subject = body.get("subject_id")
        dry = body.get("dry_run", True)
        if not subject:
            raise HTTPException(status_code=400, detail="missing subject_id")
        container = build_default_container()
        if user_id != subject and not container.rbac.has_permission(user_id, "admin"):
            raise HTTPException(status_code=403, detail="forbidden")
        task = {"id": f"privacy-{int(time.time() * 1000)}", "status": "pending", "subject": subject}
        raw = container.storage.get("privacy:tasks") or b"[]"
        arr = _json.loads(raw.decode("utf-8")) if raw else []
        arr.append(task)
        container.storage.put("privacy:tasks", _json.dumps(arr).encode("utf-8"))
        res = container.privacy_handlers.delete_subject(subject, container, dry_run=dry)
        task["status"] = "done"
        container.storage.put("privacy:tasks", _json.dumps(arr).encode("utf-8"))
        return {"status": "ok", "task": task, "result": res}

    @app.get("/api/v1/privacy/tasks/{task_id}")
    def api_privacy_task(task_id: str, request: Request):
        from fastapi import HTTPException
        from socialseed_tasker.cli.wiring import build_default_container
        import json as _json
        container = build_default_container()
        raw = container.storage.get("privacy:tasks") or b"[]"
        arr = _json.loads(raw.decode("utf-8")) if raw else []
        for t in arr:
            if t.get("id") == task_id:
                return {"status": "ok", "task": t}
        raise HTTPException(status_code=404, detail="not found")

    @app.get("/api/v1/privacy/audit")
    def api_privacy_audit(request: Request):
        from fastapi import HTTPException
        from socialseed_tasker.auth.auth import load_auth_provider
        from socialseed_tasker.cli.wiring import build_default_container
        import json as _json
        auth = request.headers.get("authorization", "")
        user_id = None
        if auth.lower().startswith("bearer "):
            user_id = load_auth_provider().verify_token(auth.split(" ", 1)[1])
        if not user_id:
            raise HTTPException(status_code=403, detail="forbidden")
        container = build_default_container()
        if not container.rbac.has_permission(user_id, "admin"):
            raise HTTPException(status_code=403, detail="forbidden")
        raw = container.storage.get("privacy:audits") or b"[]"
        arr = _json.loads(raw.decode("utf-8")) if raw else []
        return {"status": "ok", "audits": arr}

    # ML inference endpoint
    @app.post("/api/v1/models/{model_name}/infer")
    async def api_model_infer(model_name: str, request: Request):
        from fastapi import HTTPException
        from socialseed_tasker.cli.wiring import build_default_container
        from socialseed_tasker.ml.schemas import InferenceRequest
        import json as _json, time as _time
        container = build_default_container()
        raw = await request.body()
        body = _json.loads(raw.decode("utf-8")) if raw else {}
        req = InferenceRequest(**body)
        fs = container.feature_store
        features = {}
        if req.key:
            f = fs.get_features(req.key)
            if f is None:
                raise HTTPException(status_code=404, detail="feature key not found")
            features = f
        elif req.features:
            features = req.features
        else:
            raise HTTPException(status_code=400, detail="missing features or key")
        seed = req.params.get("seed") or int(os.getenv("TASKER_ML_SEED", "42"))
        runner = container.ml_runner
        start = _time.time()
        res = runner.predict(model_name, features, version=req.params.get("version"), seed=seed)
        latency = (_time.time() - start) * 1000.0
        input_hash = fs.compute_input_hash(features)
        trace = {"model": model_name, "version": res["version"], "input_hash": input_hash, "seed": res["seed"], "latency_ms": res["latency_ms"], "ts": int(_time.time())}
        try:
            raw_traces = container.storage.get("ml:traces") or b"[]"
            arr = _json.loads(raw_traces.decode("utf-8")) if raw_traces else []
            arr.append(trace)
            container.storage.put("ml:traces", _json.dumps(arr).encode("utf-8"))
        except Exception:
            pass
        from socialseed_tasker.ml.schemas import InferenceResponse
        return InferenceResponse(model=model_name, version=res["version"], prediction=res["prediction"], input_hash=input_hash, seed=res["seed"], latency_ms=res["latency_ms"], meta={})

    # Provide config to routes for policy enforcement mode
    if hasattr(repository, "_driver") and hasattr(repository._driver, "_config"):
        app.state.config = repository._driver._config
    else:
        from socialseed_tasker.application.container import AppConfig

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

    @app.exception_handler(GraphPortError)
    async def graph_port_error_handler(request: Request, exc: GraphPortError) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content=_error_response("DATABASE_CONNECTION_ERROR", str(exc)),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content=_error_response("VALIDATION_ERROR", str(exc)),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: StarletteRequest, exc: RequestValidationError) -> JSONResponse:
        errors = []
        for error in exc.errors():
            loc = error.get("loc", [])
            field_path = ".".join(str(l) for l in loc[1:] if l != "body") if loc else "unknown"
            errors.append({
                "loc": list(loc),
                "msg": error.get("msg", "validation error"),
                "type": error.get("type", "value_error"),
                "input": error.get("input"),
            })
        
        return JSONResponse(
            status_code=422,
            content={
                "data": None,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": {
                        "errors": errors,
                        "body_help": "Ensure JSON request body is valid. Check required fields for the endpoint.",
                    },
                },
                "meta": {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "request_id": str(uuid.uuid4()),
                },
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
        exc_name = type(exc).__name__
        if exc_name in ("ServiceUnavailable", "Neo4jError", "SessionExpired"):
            return JSONResponse(
                status_code=503,
                content=_error_response(
                    "DATABASE_CONNECTION_ERROR",
                    f"Database connection failed: {exc}",
                ),
            )
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
