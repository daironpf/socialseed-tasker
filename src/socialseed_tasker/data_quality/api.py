from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from socialseed_tasker.auth.permissions import require_permission
from socialseed_tasker.cli.wiring import build_default_container
from socialseed_tasker.data_quality.serializers import RuleSpec
from socialseed_tasker.infrastructure.web_api.schemas import APIResponse, Meta

router = APIRouter(prefix="/api/v1/data-quality", tags=["data-quality"])

@router.post("/rules")
def create_rule(spec: RuleSpec, request: Request) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    require_permission(request, "admin", container)
    container.rule_registry.add(spec.model_dump())
    return APIResponse(data={"rule": spec.model_dump()}, meta=Meta(request_id=None))

@router.get("/rules")
def list_rules(request: Request) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    return APIResponse(data={"rules": container.rule_registry.list()}, meta=Meta(request_id=None))

@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: str, request: Request) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    require_permission(request, "admin", container)
    if container.rule_registry.get(rule_id) is None:
        raise HTTPException(status_code=404, detail="rule not found")
    container.rule_registry.delete(rule_id)
    return APIResponse(data={"deleted": True, "rule_id": rule_id}, meta=Meta(request_id=None))

@router.get("/reports/{record_id}")
def get_report(record_id: str, request: Request) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    key = "dq:reports:" + record_id
    raw = container.storage.get(key) or b"[]"
    arr = json.loads(raw.decode("utf-8")) if raw else []
    return APIResponse(data={"report": arr}, meta=Meta(request_id=None))

@router.get("/metrics")
def get_metrics(request: Request) -> APIResponse[dict[str, Any]]:
    container: Any = build_default_container()
    raw = container.storage.get("dq:metrics") or b"{}"
    m = json.loads(raw.decode("utf-8")) if raw else {}
    return APIResponse(data={"metrics": m}, meta=Meta(request_id=None))
