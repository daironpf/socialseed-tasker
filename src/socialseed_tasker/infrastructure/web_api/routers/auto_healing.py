"""Auto-healing pipeline API (issue #520).

Endpoints consumed by the Auto-Healing Pipeline Monitor:

- ``GET    /auto-healing/runs``                      list runs (newest first)
- ``POST   /auto-healing/runs``                      start a run for an issue
- ``GET    /auto-healing/runs/{id}``                 run detail (stages, logs, patches)
- ``GET    /auto-healing/runs/{id}/logs``            run log entries
- ``GET    /auto-healing/runs/{id}/patches``         patch artifact metadata
- ``GET    /auto-healing/runs/{id}/patches/{pid}``   raw ``.patch`` download (text/plain)
- ``POST   /auto-healing/runs/{id}/cancel``          cancel a running pipeline
- ``POST   /auto-healing/runs/{id}/restart``         re-run from a stage (reverts the fix when needed)

Responses use the standard ``{data, error, meta}`` envelope and camelCase
fields matching the frontend ``types/autoHealing.ts`` contract. The patch
download endpoint returns the raw artifact as an attachment.
"""

from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from socialseed_tasker.healing.engine import (
    DEFAULT_HEALING_DIR,
    AutoHealingEngine,
    IssueLookupError,
    RunConflictError,
    RunNotFoundError,
)
from socialseed_tasker.healing.storage import HealingStorage
from socialseed_tasker.infrastructure.web_api.schemas import APIResponse, Meta

auto_healing_router = APIRouter()


class CamelModel(BaseModel):
    """Response/request model serialised to camelCase (frontend contract)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class StageResponse(CamelModel):
    id: str
    label: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_ms: int | None = None
    details: str | None = None


class PatchResponse(CamelModel):
    id: str
    run_id: str
    stage_id: str
    strategy: str
    filename: str
    files: list[str]
    created_at: str
    size_bytes: int
    commit_sha: str


class LogResponse(CamelModel):
    id: str
    run_id: str
    timestamp: str
    source: str
    content: str


class RunResponse(CamelModel):
    id: str
    issue_id: str
    issue_title: str
    repo: str
    branch: str
    commit_sha: str
    stages: list[StageResponse]
    current_stage_index: int
    started_at: str
    completed_at: str | None = None
    status: str
    pr_url: str | None = None
    neo4j_node_id: str | None = None
    created_issue_id: str | None = None
    patches: list[PatchResponse] = Field(default_factory=list)
    logs: list[LogResponse] = Field(default_factory=list)


class StartRunRequest(CamelModel):
    issue_id: str = Field(..., min_length=1, description="Anchor issue id in Neo4j")


class RestartRequest(CamelModel):
    stage_id: str | None = Field(None, description="Stage to restart from (default: first incomplete)")


def _engine(request: Request) -> AutoHealingEngine:
    engine = getattr(request.app.state, "auto_healing", None)
    if engine is None:
        base_dir = os.getenv("TASKER_HEALING_DIR") or DEFAULT_HEALING_DIR
        engine = AutoHealingEngine(
            HealingStorage(base_dir),
            repo_provider=lambda: getattr(request.app.state, "repository", None),
        )
        request.app.state.auto_healing = engine
    return engine


def _run_response(run: dict[str, Any]) -> RunResponse:
    return RunResponse.model_validate(run)


def _not_found(run_id: str) -> HTTPException:
    return HTTPException(status_code=404, detail=f"run {run_id} not found")


@auto_healing_router.get(
    "/auto-healing/runs",
    response_model=APIResponse[list[RunResponse]],
    summary="List auto-healing pipeline runs",
)
def list_pipeline_runs(request: Request) -> APIResponse[list[RunResponse]]:
    runs = [_run_response(run) for run in _engine(request).list_runs()]
    return APIResponse(data=runs, meta=Meta(request_id=None))


@auto_healing_router.post(
    "/auto-healing/runs",
    status_code=201,
    response_model=APIResponse[RunResponse],
    summary="Start an auto-healing pipeline run",
    description="Creates a run anchored to an existing issue and starts executing its stages.",
)
async def start_pipeline_run(body: StartRunRequest, request: Request) -> APIResponse[RunResponse]:
    engine = _engine(request)
    try:
        run = await engine.create_run(body.issue_id)
    except IssueLookupError:
        raise HTTPException(status_code=404, detail=f"issue {body.issue_id} not found") from None
    except RunConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return APIResponse(data=_run_response(run), meta=Meta(request_id=None))


@auto_healing_router.get(
    "/auto-healing/runs/{run_id}",
    response_model=APIResponse[RunResponse],
    summary="Get an auto-healing run",
)
def get_pipeline_run(run_id: str, request: Request) -> APIResponse[RunResponse]:
    try:
        run = _engine(request).get_run(run_id)
    except RunNotFoundError:
        raise _not_found(run_id) from None
    return APIResponse(data=_run_response(run), meta=Meta(request_id=None))


@auto_healing_router.get(
    "/auto-healing/runs/{run_id}/logs",
    response_model=APIResponse[list[LogResponse]],
    summary="Get auto-healing run logs",
)
def get_pipeline_logs(run_id: str, request: Request) -> APIResponse[list[LogResponse]]:
    try:
        run = _engine(request).get_run(run_id)
    except RunNotFoundError:
        raise _not_found(run_id) from None
    logs = [LogResponse.model_validate(entry) for entry in run.get("logs") or []]
    return APIResponse(data=logs, meta=Meta(request_id=None))


@auto_healing_router.get(
    "/auto-healing/runs/{run_id}/patches",
    response_model=APIResponse[list[PatchResponse]],
    summary="List patch artifacts of a run",
)
def list_pipeline_patches(run_id: str, request: Request) -> APIResponse[list[PatchResponse]]:
    try:
        patches = _engine(request).list_patches(run_id)
    except RunNotFoundError:
        raise _not_found(run_id) from None
    data = [PatchResponse.model_validate(meta) for meta in patches]
    return APIResponse(data=data, meta=Meta(request_id=None))


@auto_healing_router.get(
    "/auto-healing/runs/{run_id}/patches/{patch_id}",
    summary="Download a .patch artifact",
    description="Returns the raw unified diff applied to the workspace repository as a file attachment.",
    responses={200: {"content": {"text/plain": {}}}},
)
def download_patch(run_id: str, patch_id: str, request: Request) -> Response:
    engine = _engine(request)
    try:
        patches = engine.list_patches(run_id)
    except RunNotFoundError:
        raise _not_found(run_id) from None
    if not any(meta["id"] == patch_id for meta in patches):
        raise HTTPException(status_code=404, detail="patch not found")
    result = engine.read_patch(run_id, patch_id)
    if result is None:
        raise HTTPException(status_code=404, detail="patch artifact missing on disk")
    content, filename = result
    return Response(
        content=content,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@auto_healing_router.post(
    "/auto-healing/runs/{run_id}/cancel",
    response_model=APIResponse[RunResponse],
    summary="Cancel a running pipeline",
)
async def cancel_pipeline_run(run_id: str, request: Request) -> APIResponse[RunResponse]:
    engine = _engine(request)
    try:
        run = engine.cancel(run_id)
    except RunNotFoundError:
        raise _not_found(run_id) from None
    except RunConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return APIResponse(data=_run_response(run), meta=Meta(request_id=None))


@auto_healing_router.post(
    "/auto-healing/runs/{run_id}/restart",
    response_model=APIResponse[RunResponse],
    summary="Restart a pipeline from a stage",
    description=(
        "Resets the run from the given stage (default: first incomplete stage). "
        "Re-running from the fix stage restores the pre-fix workspace backup "
        "and drops the previous patch artifacts."
    ),
)
async def restart_pipeline_run(
    run_id: str,
    request: Request,
    body: RestartRequest | None = None,
) -> APIResponse[RunResponse]:
    engine = _engine(request)
    stage_id = body.stage_id if body else None
    try:
        run = await engine.restart(run_id, stage_id)
    except RunNotFoundError:
        raise _not_found(run_id) from None
    except RunConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    return APIResponse(data=_run_response(run), meta=Meta(request_id=None))
