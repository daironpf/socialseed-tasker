"""API router for the workflow definition library (issue #575).

Builtin ``.md`` definitions imported at boot are read-only; custom workflows
belong to the creating user (``created_by`` from the JWT sub, pattern #569).
This is a definitions library only — no execution engine (out of scope).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from socialseed_tasker.auth.user_store import PostgresWorkflowStore
from socialseed_tasker.config.storage import get_database_url
from socialseed_tasker.infrastructure.web_api.routers.chat import _resolve_user
from socialseed_tasker.infrastructure.web_api.schemas import (
    APIResponse,
    Meta,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowSource,
    WorkflowUpdate,
)

workflows_router = APIRouter()


def _pg_store() -> PostgresWorkflowStore:
    """PostgreSQL store for /workflows (issue #575)."""
    database_url = get_database_url()
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL not configured: TASKER_DATABASE_URL is not set",
        )
    return PostgresWorkflowStore(database_url)


def _to_response(workflow: dict[str, Any]) -> WorkflowResponse:
    return WorkflowResponse(
        slug=str(workflow["slug"]),
        name=str(workflow["name"]),
        description=workflow.get("description"),
        source=workflow.get("source") or "custom",
        created_by=workflow.get("created_by"),
        created_at=workflow.get("created_at"),
        updated_at=workflow.get("updated_at"),
        content_md=workflow.get("content_md"),
        steps=workflow.get("steps"),
    )


@workflows_router.get(
    "/workflows",
    response_model=APIResponse[list[WorkflowResponse]],
    summary="List workflow definitions",
    description="List the workflow library, optionally filtered by source (issue #575).",
)
def list_workflows(source: WorkflowSource | None = Query(None)) -> APIResponse[list[WorkflowResponse]]:  # noqa: B008
    """List workflows (summary rows without content_md)."""
    workflows = _pg_store().list_workflows(source=source)
    return APIResponse(data=[_to_response(w) for w in workflows], meta=Meta(request_id=None))


@workflows_router.get(
    "/workflows/{slug}",
    response_model=APIResponse[WorkflowResponse],
    summary="Get workflow definition",
    description="Full definition with content_md + steps (issue #575).",
)
def get_workflow(slug: str) -> APIResponse[WorkflowResponse]:
    """Get one workflow by slug; 404 when missing."""
    workflow = _pg_store().get_workflow(slug)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return APIResponse(data=_to_response(workflow), meta=Meta(request_id=None))


@workflows_router.post(
    "/workflows",
    response_model=APIResponse[WorkflowResponse],
    status_code=201,
    summary="Create custom workflow",
    description="Create a custom workflow; created_by comes from the JWT sub (issue #575).",
)
def create_workflow(body: WorkflowCreate, request: Request) -> APIResponse[WorkflowResponse]:
    """Create a custom workflow; 409 when the slug is already taken."""
    try:
        workflow = _pg_store().create_workflow(
            slug=body.slug,
            name=body.name,
            description=body.description,
            content_md=body.content_md,
            steps=body.steps,
            created_by=_resolve_user(request),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail="slug already exists") from exc
    return APIResponse(data=_to_response(workflow), meta=Meta(request_id=None))


@workflows_router.put(
    "/workflows/{slug}",
    response_model=APIResponse[WorkflowResponse],
    summary="Update custom workflow",
    description="Partially update a custom workflow; builtin rows are read-only (issue #575).",
)
def update_workflow(slug: str, body: WorkflowUpdate) -> APIResponse[WorkflowResponse]:
    """Update a custom workflow; 404 missing, 409 builtin."""
    try:
        workflow = _pg_store().update_workflow(
            slug,
            name=body.name,
            description=body.description,
            content_md=body.content_md,
            steps=body.steps,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Workflow not found") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail="builtin workflow") from exc
    return APIResponse(data=_to_response(workflow), meta=Meta(request_id=None))


@workflows_router.delete(
    "/workflows/{slug}",
    summary="Delete custom workflow",
    description="Delete a custom workflow; builtin rows are read-only (issue #575).",
)
def delete_workflow(slug: str) -> APIResponse[bool]:
    """Delete a custom workflow; 404 missing, 409 builtin."""
    try:
        deleted = _pg_store().delete_workflow(slug)
    except PermissionError as exc:
        raise HTTPException(status_code=409, detail="builtin workflow") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return APIResponse(data=True, meta=Meta(request_id=None))
