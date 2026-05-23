from __future__ import annotations
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel, Field
from socialseed_tasker.cli.wiring import build_default_container

router = APIRouter(prefix="/api/v1/registry", tags=["registry"])


class RegisterSchemaRequest(BaseModel):
    name: str
    version: str
    schema_data: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    compatibility: str = "BACKWARD"


class RegisterDatasetRequest(BaseModel):
    dataset_id: str
    title: str
    description: str
    schema_name: str
    default_schema_version: str
    owner: str
    tags: list[str] = []


@router.post("/schemas")
def register_schema(req: RegisterSchemaRequest):
    container = build_default_container()
    reg = container.schema_registry
    try:
        reg.register_schema(req.name, req.version, req.schema_data, compatibility=req.compatibility)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@router.get("/schemas/{name}/versions")
def list_versions(name: str):
    container = build_default_container()
    reg = container.schema_registry
    return {"status": "ok", "versions": reg.get_versions(name)}


@router.get("/schemas/{name}/{version}")
def get_schema(name: str, version: str):
    container = build_default_container()
    reg = container.schema_registry
    try:
        s = reg.get_schema(name, version)
    except KeyError:
        raise HTTPException(status_code=404, detail="schema not found")
    return {"status": "ok", "schema": s}


@router.post("/datasets")
def register_dataset(req: RegisterDatasetRequest):
    container = build_default_container()
    reg = container.schema_registry
    try:
        reg.register_dataset(req.dataset_id, req.title, req.description, req.schema_name, req.default_schema_version, req.owner, tags=req.tags)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"status": "ok"}


@router.get("/datasets")
def list_datasets():
    container = build_default_container()
    reg = container.schema_registry
    return {"status": "ok", "datasets": reg.list_datasets()}


@router.get("/datasets/{dataset_id}")
def get_dataset(dataset_id: str):
    container = build_default_container()
    reg = container.schema_registry
    try:
        d = reg.get_dataset(dataset_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="dataset not found")
    return {"status": "ok", "dataset": d}
