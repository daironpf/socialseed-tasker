from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from socialseed_tasker.cli.wiring import build_default_container
from socialseed_tasker.infrastructure.web_api.schemas import APIResponse, Meta

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])


class RegisterSchemaRequest(BaseModel):
    name: str
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", description="Semantic version MAJOR.MINOR.PATCH")
    schema_data: dict[str, Any] = Field(default_factory=dict, alias="schema")
    compatibility: str = "BACKWARD"


class RegisterDatasetRequest(BaseModel):
    dataset_id: str
    title: str
    description: str
    schema_name: str
    default_schema_version: str
    owner: str
    tags: list[str] = []


def _meta() -> Meta:
    return Meta(request_id=None)


@router.post("/schemas")
def register_schema(req: RegisterSchemaRequest) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    reg = container.schema_registry
    try:
        reg.register_schema(req.name, req.version, req.schema_data, compatibility=req.compatibility)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIResponse(data={"name": req.name, "version": req.version}, meta=_meta())


@router.get("/schemas/{name}/versions")
def list_versions(name: str) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    reg = container.schema_registry
    return APIResponse(data={"versions": reg.get_versions(name)}, meta=_meta())


@router.get("/schemas/{name}/{version}")
def get_schema(name: str, version: str) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    reg = container.schema_registry
    try:
        s = reg.get_schema(name, version)
    except KeyError:
        raise HTTPException(status_code=404, detail="schema not found") from None
    return APIResponse(data={"schema": s}, meta=_meta())


@router.delete("/schemas/{name}")
def delete_schema(name: str) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    reg = container.schema_registry
    try:
        reg.delete_schema(name)
    except KeyError:
        raise HTTPException(status_code=404, detail="schema not found") from None
    return APIResponse(data={"deleted": True, "name": name}, meta=_meta())


@router.post("/datasets")
def register_dataset(req: RegisterDatasetRequest) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    reg = container.schema_registry
    try:
        reg.register_dataset(
            req.dataset_id,
            req.title,
            req.description,
            req.schema_name,
            req.default_schema_version,
            req.owner,
            tags=req.tags,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return APIResponse(data={"dataset_id": req.dataset_id}, meta=_meta())


@router.get("/datasets")
def list_datasets() -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    reg = container.schema_registry
    return APIResponse(data={"datasets": reg.list_datasets()}, meta=_meta())


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    reg = container.schema_registry
    try:
        d = reg.get_dataset(dataset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="dataset not found") from None
    return APIResponse(data={"dataset": d}, meta=_meta())


@router.delete("/datasets/{dataset_id}")
def delete_dataset(dataset_id: str) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    reg = container.schema_registry
    try:
        reg.delete_dataset(dataset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="dataset not found") from None
    return APIResponse(data={"deleted": True, "dataset_id": dataset_id}, meta=_meta())
