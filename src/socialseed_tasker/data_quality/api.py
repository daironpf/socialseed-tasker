from __future__ import annotations

import json

from fastapi import APIRouter, Request

from socialseed_tasker.auth.permissions import require_permission
from socialseed_tasker.cli.wiring import build_default_container
from socialseed_tasker.data_quality.serializers import RuleSpec

router = APIRouter(prefix="/api/v1/data-quality", tags=["data-quality"])

@router.post("/rules")
def create_rule(spec: RuleSpec, request: Request):
    container = build_default_container()
    require_permission(request, "admin", container)
    container.rule_registry.add(spec.model_dump())
    return {"status": "ok", "rule": spec.model_dump()}

@router.get("/rules")
def list_rules(request: Request):
    container = build_default_container()
    return {"status": "ok", "rules": container.rule_registry.list()}

@router.get("/reports/{record_id}")
def get_report(record_id: str, request: Request):
    container = build_default_container()
    key = "dq:reports:" + record_id
    raw = container.storage.get(key) or b"[]"
    arr = json.loads(raw.decode("utf-8")) if raw else []
    return {"status": "ok", "report": arr}

@router.get("/metrics")
def get_metrics(request: Request):
    container = build_default_container()
    raw = container.storage.get("dq:metrics") or b"{}"
    m = json.loads(raw.decode("utf-8")) if raw else {}
    return {"status": "ok", "metrics": m}
