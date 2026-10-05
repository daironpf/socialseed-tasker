"""Setup wizard endpoints: install status and first-run initialization (issue #543).

- ``GET  /setup/status``    reports ``installed`` / ``needSetup``. The truth is
  the presence of a ``:Project`` node with ``initialized_at`` in Neo4j (set by
  ``POST /setup/initialize``) or the ``TASKER_INSTALLED=true`` environment
  override at boot. When Neo4j is unreachable the endpoint degrades safely and
  answers from the environment flag only.
- ``POST /setup/initialize`` first wipes every database of any data that does
  not belong to a fresh installation (Neo4j nodes, PostgreSQL public tables,
  MongoDB chat and notification collections and the Redis session/cache DB),
  then creates the administrator (PostgreSQL bcrypt via :func:`create_user`
  plus a ``:User`` node with ``role='ADMIN'``), the root ``:Project`` node and
  the selected governance policies linked with the existing
  ``(Project)-[:ENFORCES]->(Policy)`` model, and finally seeds the admin's
  ``WELCOME`` notification (issue #549). Returns 403 when the system is
  already installed.

State is provided by :class:`Neo4jSetupStore` on ``app.state.setup_store`` so
tests can swap it for an in-memory fake (pattern of ``chat_repository``).
"""

from __future__ import annotations

import logging
import os
import secrets
import uuid
from datetime import datetime, timezone
from typing import Any, Protocol
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from starlette.concurrency import run_in_threadpool

from socialseed_tasker.auth.user_store import create_user, normalize_username, wipe_postgres_data
from socialseed_tasker.config.storage import get_mongo_url, get_redis_url
from socialseed_tasker.infrastructure.mongo.client import DEFAULT_CHAT_DB
from socialseed_tasker.infrastructure.mongo.notification_repository import (
    NotificationMongoRepository,
    NotificationStoreError,
)
from socialseed_tasker.infrastructure.web_api.schemas import APIResponse
from socialseed_tasker.models.notification import (
    Notification,
    NotificationSeverity,
    NotificationType,
)

logger = logging.getLogger(__name__)

setup_router = APIRouter(tags=["setup"])

DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"

# Master API key issued for external agents (Cursor, Claude, Windsurf, ...).
# Persisted in the secrets store so the auth middleware can accept it after a
# restart (issue #546).
MASTER_KEY_PREFIX = "tasker_sk_live_"
MASTER_KEY_SECRET_NAME = "master_api_key"

PREDEFINED_POLICIES: dict[str, dict[str, str]] = {
    "prevent_circular_dependencies": {
        "name": "Prevent circular dependencies",
        "description": "Prevenir dependencias circulares en el grafo",
        "severity": "BLOCKER",
        "target_scope": "PROJECT",
        "logic_definition": '{"type": "no_circular_dependencies"}',
    },
    "require_solution_summary": {
        "name": "Require solution summary",
        "description": "Exigir resumen de solucion y archivos afectados antes de cerrar un issue",
        "severity": "WARNING",
        "target_scope": "PROJECT",
        "logic_definition": '{"type": "require_solution_summary_on_close"}',
    },
    "require_human_approval_core": {
        "name": "Require human approval for core changes",
        "description": "Aprobacion humana obligatoria para modificaciones en el Core",
        "severity": "BLOCKER",
        "target_scope": "COMPONENT",
        "logic_definition": '{"type": "require_human_approval", "target": "core"}',
    },
}

CREATE_ADMIN_NODE = """
MERGE (u:User {username: $username})
ON CREATE SET u.id = $id, u.role = 'ADMIN', u.createdAt = $now
ON MATCH SET u.role = 'ADMIN'
"""

CREATE_ROOT_PROJECT = """
MERGE (p:Project {name: $name})
ON CREATE SET p.id = $id, p.summary = $summary, p.initialized_at = datetime(), p.createdAt = $now
ON MATCH SET p.id = coalesce(p.id, $id), p.summary = $summary,
    p.initialized_at = coalesce(p.initialized_at, datetime())
RETURN p.id AS id
"""

UPSERT_POLICY_LINK = """
MERGE (p:Policy {name: $name})
ON CREATE SET p.id = $id, p.description = $description, p.severity = $severity,
    p.target_scope = $target_scope, p.logic_definition = $logic_definition,
    p.is_active = true, p.createdAt = $now, p.updatedAt = $now
ON MATCH SET p.updatedAt = $now
WITH p
MATCH (proj:Project {id: $projectId})
MERGE (proj)-[:ENFORCES]->(p)
"""

QUERY_INITIALIZED_PROJECT = """
MATCH (p:Project)
WHERE p.initialized_at IS NOT NULL
RETURN p.name AS name
LIMIT 1
"""

QUERY_NODE_COUNT = "MATCH (n) RETURN count(n) AS c"

WIPE_ALL_NODES = "MATCH (n) DETACH DELETE n"


class SetupStoreError(RuntimeError):
    """Raised when the setup state backend cannot be reached."""


class SetupStore(Protocol):
    """State backend for the install flag and first-run writes."""

    def installed(self) -> bool:
        ...

    def node_count(self) -> int:
        ...

    def wipe(self) -> None:
        ...

    def initialize(
        self,
        *,
        admin_username: str,
        project_name: str,
        project_summary: str,
        policies: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ...


class Neo4jSetupStore:
    """Setup state persisted in Neo4j (initialized project root node)."""

    def __init__(self, driver: Any | None = None) -> None:
        self._driver = driver

    def _open_session(self) -> Any:
        driver = self._driver
        if driver is None:
            from socialseed_tasker.application.wiring import get_driver

            driver = get_driver()
        if driver is None:
            raise SetupStoreError("Neo4j is not configured")
        actual = driver.driver if hasattr(driver, "driver") else driver
        database = driver.database if hasattr(driver, "database") else "neo4j"
        return actual.session(database=database)

    def installed(self) -> bool:
        try:
            with self._open_session() as session:
                result = session.run(QUERY_INITIALIZED_PROJECT)
                return result.single() is not None
        except SetupStoreError:
            raise
        except Exception as exc:
            raise SetupStoreError(str(exc)) from exc

    def node_count(self) -> int:
        try:
            with self._open_session() as session:
                result = session.run(QUERY_NODE_COUNT)
                record = result.single()
                return int(record["c"]) if record else 0
        except SetupStoreError:
            raise
        except Exception as exc:
            raise SetupStoreError(str(exc)) from exc

    def wipe(self) -> None:
        try:
            with self._open_session() as session:
                session.run(WIPE_ALL_NODES)
        except SetupStoreError:
            raise
        except Exception as exc:
            raise SetupStoreError(str(exc)) from exc

    def initialize(
        self,
        *,
        admin_username: str,
        project_name: str,
        project_summary: str,
        policies: list[dict[str, Any]],
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        generated_project_id = str(uuid.uuid4())
        try:
            with self._open_session() as session:
                session.run(
                    CREATE_ADMIN_NODE,
                    id=str(uuid.uuid4()),
                    username=admin_username,
                    now=now,
                )
                record = session.run(
                    CREATE_ROOT_PROJECT,
                    id=generated_project_id,
                    name=project_name,
                    summary=project_summary,
                    now=now,
                ).single()
                project_id = str(record["id"]) if record and record.get("id") else generated_project_id
                for spec in policies:
                    session.run(
                        UPSERT_POLICY_LINK,
                        projectId=project_id,
                        id=str(uuid.uuid4()),
                        name=spec["name"],
                        description=spec.get("description", ""),
                        severity=spec.get("severity", "WARNING"),
                        target_scope=spec.get("target_scope", "PROJECT"),
                        logic_definition=spec.get("logic_definition"),
                        now=now,
                    )
        except SetupStoreError:
            raise
        except Exception as exc:
            raise SetupStoreError(str(exc)) from exc
        return {"projectId": project_id, "generatedId": generated_project_id}


class CamelModel(BaseModel):
    """Request/response model serialised to camelCase (frontend contract)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SetupStatusResponse(CamelModel):
    installed: bool
    need_setup: bool


class SetupPayload(CamelModel):
    admin_user: str = ""
    admin_password: str = ""
    project_name: str = ""
    project_summary: str = ""
    policies: list[str] = Field(default_factory=list)
    custom_policies: list[str] = Field(default_factory=list)
    # Optional AI agent credentials (issue #546): an empty api_key makes the
    # backend generate a fresh master key; mcp_port 0 means "auto" (the port
    # of the API origin the client is connected to).
    api_key: str = ""
    mcp_port: int = Field(default=0, ge=0, le=65535)
    # Explicit wipe consent: initialize refuses to wipe a populated graph
    # unless the caller confirms (protects against accidental reinstalls).
    confirm_wipe: bool = False


class SetupInitializeResponse(CamelModel):
    installed: bool
    admin_username: str
    project_name: str
    project_id: str
    policies: list[str]
    credentials: str
    api_key: str
    mcp_port: int


def _env_installed() -> bool:
    return os.getenv("TASKER_INSTALLED", "false").strip().lower() == "true"


def _store(request: Request) -> SetupStore:
    store: SetupStore | None = getattr(request.app.state, "setup_store", None)
    if store is None:
        store = Neo4jSetupStore()
        request.app.state.setup_store = store
    return store


def _installed(store: SetupStore) -> bool:
    if _env_installed():
        return True
    try:
        return bool(store.installed())
    except SetupStoreError as exc:
        logger.warning("setup status degraded (answering from env only): %s", exc)
        return False


def _wipe_mongo() -> None:
    """Drop every Mongo collection so the install starts from a pristine DB.

    The loop drops *all* non-system collections of the chat database —
    including ``notifications`` (issue #549) — so every reinstall ends with
    exactly one fresh welcome notification.
    """
    url = get_mongo_url()
    if not url:
        return
    try:
        from pymongo import MongoClient

        client: Any = MongoClient(url, serverSelectionTimeoutMS=2000)
        try:
            db_name = (
                os.getenv("TASKER_MONGO_DB")
                or urlparse(url).path.lstrip("/").split("?")[0]
                or DEFAULT_CHAT_DB
            )
            db = client[db_name]
            for name in db.list_collection_names():
                if not name.startswith("system."):
                    db.drop_collection(name)
        finally:
            client.close()
    except Exception as exc:
        logger.warning("mongo wipe failed (continuing): %s", exc)


def _wipe_redis() -> None:
    """Flush the session/cache Redis DB so no stale development state survives."""
    url = get_redis_url()
    if not url:
        return
    try:
        import redis as redis_lib

        client = redis_lib.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        try:
            client.flushdb()
        finally:
            client.close()
    except Exception as exc:
        logger.warning("redis wipe failed (continuing): %s", exc)


def _resolve_policies(payload: SetupPayload) -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    for key in payload.policies:
        normalized_key = key.strip()
        spec = PREDEFINED_POLICIES.get(normalized_key)
        if spec is None:
            raise HTTPException(status_code=400, detail=f"Unknown policy '{key}'")
        specs.append({"key": normalized_key, **spec})
    for text in payload.custom_policies:
        rule = text.strip()
        if not rule:
            continue
        specs.append(
            {
                "key": f"custom:{rule[:40]}",
                "name": rule[:100],
                "description": rule,
                "severity": "WARNING",
                "target_scope": "PROJECT",
                "logic_definition": '{"type": "custom_rule"}',
            }
        )
    return specs


def _generate_master_api_key() -> str:
    return MASTER_KEY_PREFIX + secrets.token_urlsafe(32)


def _persist_master_key(request: Request, api_key: str, mcp_port: int) -> None:
    """Expose the key to this process and persist it in the secrets store.

    The auth middleware accepts the key from ``app.state`` right away; the
    secrets store copy lets it keep working after an API restart. Failures
    degrade to the in-process key only (the installation still succeeds).
    """
    request.app.state.master_api_key = api_key
    request.app.state.master_api_key_loaded = True
    try:
        from socialseed_tasker.cli.wiring import build_default_container

        container: Any = build_default_container()
        container.secrets_store.put_secret(
            MASTER_KEY_SECRET_NAME,
            api_key.encode("utf-8"),
            metadata={"mcpPort": mcp_port, "source": "setup"},
            actor="setup",
        )
    except Exception as exc:
        logger.warning("master api key persistence failed (continuing): %s", exc)


async def _insert_welcome_notification(request: Request, admin_username: str) -> None:
    """Seed the admin's post-install welcome notification (issue #549).

    Degrades safely: a missing/unreachable MongoDB (typed
    :class:`NotificationStoreError`) is logged and skipped so the
    installation still succeeds. Idempotency guard by ``(user_id, type)``:
    an existing ``WELCOME`` for the admin is never duplicated (covers a
    rerun whose wipe did not clear the collection).
    """
    repository: NotificationMongoRepository | None = getattr(
        request.app.state, "notification_repository", None
    )
    if repository is None:
        logger.warning("welcome notification skipped (continuing install): store unavailable")
        return
    try:
        _, total = await repository.list_for_user(
            admin_username,
            notification_type=NotificationType.WELCOME.value,
            limit=1,
        )
        if total > 0:
            logger.info(
                "welcome notification already present for %s (skipped)", admin_username
            )
            return
        welcome = Notification(
            user_id=admin_username,
            type=NotificationType.WELCOME,
            severity=NotificationSeverity.INFO,
            title="¡Bienvenido a SocialSeed Tasker!",
            message=(
                "El sistema ha sido instalado correctamente. Te recomendamos "
                "crear tus primeros agentes de IA y registrar usuarios en la "
                "plataforma."
            ),
            channel="system",
            requires_action=True,
            link_to="/users",
        )
        await repository.insert(welcome)
        logger.info("welcome notification inserted for %s", admin_username)
    except NotificationStoreError as exc:
        logger.warning("welcome notification skipped (continuing install): %s", exc)


@setup_router.get(
    "/setup/status",
    response_model=APIResponse[SetupStatusResponse],
    summary="First-run installation status",
    description="Reports whether Tasker is installed; consumed by the setup wizard router guard (issue #544).",
)
def setup_status(request: Request) -> APIResponse[SetupStatusResponse]:
    installed = _installed(_store(request))
    data = SetupStatusResponse(installed=installed, need_setup=not installed)
    return APIResponse[SetupStatusResponse](data=data)


@setup_router.post(
    "/setup/initialize",
    response_model=APIResponse[SetupInitializeResponse],
    summary="Run the first-run initialization",
    description=(
        "Wipes any data that does not belong to the installation (Neo4j, PostgreSQL, MongoDB chat "
        "and notifications, and Redis), then creates the administrator (PostgreSQL bcrypt + :User "
        "ADMIN node), the root :Project and the selected governance policies, and seeds the admin's "
        "WELCOME notification; returns 403 when already installed (issues #543/#545/#549)."
    ),
)
async def setup_initialize(
    payload: SetupPayload, request: Request
) -> APIResponse[SetupInitializeResponse]:
    # The install itself (Neo4j sync sessions, bcrypt, pymongo/redis wipes)
    # keeps running on a worker thread exactly as before (issue #543); only
    # the async welcome notification runs on the event loop (issue #549).
    data = await run_in_threadpool(_perform_initialize, payload, request)
    await _insert_welcome_notification(request, data.admin_username)
    return APIResponse[SetupInitializeResponse](data=data)


def _perform_initialize(payload: SetupPayload, request: Request) -> SetupInitializeResponse:
    store = _store(request)
    # Fail closed: a wipe must never run on a degraded status check. If the
    # store cannot answer, the caller must retry instead of reinstalling.
    try:
        already_installed = _env_installed() or store.installed()
    except SetupStoreError as exc:
        raise HTTPException(
            status_code=503, detail=f"Setup state backend unavailable: {exc}"
        ) from exc
    if already_installed:
        raise HTTPException(status_code=403, detail="Tasker is already installed")

    # Refuse to wipe a populated system without explicit consent. This is an
    # independent signal from the installed flag: a degraded or stale read
    # that reports "not installed" must not silently destroy existing data.
    try:
        existing_nodes = store.node_count()
    except SetupStoreError as exc:
        raise HTTPException(
            status_code=503, detail=f"Setup state backend unavailable: {exc}"
        ) from exc
    if existing_nodes > 0 and not payload.confirm_wipe:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Refusing to wipe a system with {existing_nodes} nodes: "
                "resend with confirm_wipe=true to proceed"
            ),
        )

    admin_username = normalize_username(payload.admin_user) or DEFAULT_ADMIN_USER
    admin_password = payload.admin_password or DEFAULT_ADMIN_PASSWORD
    project_name = payload.project_name.strip()
    if not project_name:
        raise HTTPException(status_code=400, detail="project_name is required")
    specs = _resolve_policies(payload)

    try:
        store.wipe()
    except SetupStoreError as exc:
        raise HTTPException(status_code=503, detail=f"Setup state backend unavailable: {exc}") from exc
    try:
        wipe_postgres_data()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"PostgreSQL wipe failed: {exc}") from exc
    _wipe_mongo()
    _wipe_redis()

    credentials = create_user(
        username=admin_username,
        password=admin_password,
        role="ADMIN",
        user_type="admin",
    )

    try:
        record = store.initialize(
            admin_username=admin_username,
            project_name=project_name,
            project_summary=payload.project_summary.strip(),
            policies=specs,
        )
    except SetupStoreError as exc:
        raise HTTPException(status_code=503, detail=f"Setup state backend unavailable: {exc}") from exc

    master_api_key = payload.api_key.strip() or _generate_master_api_key()
    _persist_master_key(request, master_api_key, payload.mcp_port)

    data = SetupInitializeResponse(
        installed=True,
        admin_username=admin_username,
        project_name=project_name,
        project_id=str(record.get("projectId", "")),
        policies=[str(spec["name"]) for spec in specs],
        credentials=credentials,
        api_key=master_api_key,
        mcp_port=payload.mcp_port,
    )
    return data
