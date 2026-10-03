"""Setup wizard endpoints: install status and first-run initialization (issue #543).

- ``GET  /setup/status``    reports ``installed`` / ``needSetup``. The truth is
  the presence of a ``:Project`` node with ``initialized_at`` in Neo4j (set by
  ``POST /setup/initialize``) or the ``TASKER_INSTALLED=true`` environment
  override at boot. When Neo4j is unreachable the endpoint degrades safely and
  answers from the environment flag only.
- ``POST /setup/initialize`` creates the administrator (PostgreSQL bcrypt via
  :func:`create_user` plus a ``:User`` node with ``role='ADMIN'``), the root
  ``:Project`` node and the selected governance policies linked with the
  existing ``(Project)-[:ENFORCES]->(Policy)`` model. Returns 403 when the
  system is already installed.

State is provided by :class:`Neo4jSetupStore` on ``app.state.setup_store`` so
tests can swap it for an in-memory fake (pattern of ``chat_repository``).
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any, Protocol

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from socialseed_tasker.auth.user_store import create_user, normalize_username
from socialseed_tasker.infrastructure.web_api.schemas import APIResponse

setup_router = APIRouter(tags=["setup"])

DEFAULT_ADMIN_USER = "admin"
DEFAULT_ADMIN_PASSWORD = "admin"

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


class SetupStoreError(RuntimeError):
    """Raised when the setup state backend cannot be reached."""


class SetupStore(Protocol):
    """State backend for the install flag and first-run writes."""

    def installed(self) -> bool:
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


class SetupInitializeResponse(CamelModel):
    installed: bool
    admin_username: str
    project_name: str
    project_id: str
    policies: list[str]
    credentials: str


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
    except SetupStoreError:
        return False


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
        "Creates the administrator (PostgreSQL bcrypt + :User ADMIN node), the root :Project "
        "and the selected governance policies; returns 403 when already installed (issue #543)."
    ),
)
def setup_initialize(payload: SetupPayload, request: Request) -> APIResponse[SetupInitializeResponse]:
    store = _store(request)
    if _installed(store):
        raise HTTPException(status_code=403, detail="Tasker is already installed")

    admin_username = normalize_username(payload.admin_user) or DEFAULT_ADMIN_USER
    admin_password = payload.admin_password or DEFAULT_ADMIN_PASSWORD
    project_name = payload.project_name.strip()
    if not project_name:
        raise HTTPException(status_code=400, detail="project_name is required")
    specs = _resolve_policies(payload)

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

    data = SetupInitializeResponse(
        installed=True,
        admin_username=admin_username,
        project_name=project_name,
        project_id=str(record.get("projectId", "")),
        policies=[str(spec["name"]) for spec in specs],
        credentials=credentials,
    )
    return APIResponse[SetupInitializeResponse](data=data)
