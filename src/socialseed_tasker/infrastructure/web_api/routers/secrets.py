from __future__ import annotations

import base64
import json
import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException

from socialseed_tasker.cli.wiring import build_default_container

logger = logging.getLogger(__name__)

secrets_router = APIRouter()


def _get_container():
    return build_default_container()


def _check_permission(
    container: Any, user_id: str | None, permission: str
) -> None:
    if not user_id:
        raise HTTPException(status_code=403, detail="forbidden")
    if not container.rbac.has_permission(user_id, permission):
        raise HTTPException(status_code=403, detail="forbidden")


@secrets_router.post("/api/v1/secrets")
def api_put_secret(
    req: dict = Body(...),
    container=Depends(_get_container),
) -> dict:
    name = req.get("name")
    val_b64 = req.get("value")
    meta = req.get("metadata", {})
    if not name or not val_b64:
        raise HTTPException(status_code=400, detail="missing name or value")
    val = base64.b64decode(val_b64.encode("utf-8"))
    container.secrets_store.put_secret(
        name, val, metadata=meta, actor="api"
    )
    return {"status": "ok"}


@secrets_router.get("/api/v1/secrets/{name}")
def api_get_secret_meta(
    name: str,
    container=Depends(_get_container),
) -> dict:
    try:
        res = container.secrets_store.get_secret(name, reveal=False)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")
    return {
        "status": "ok",
        "metadata": res["metadata"],
        "ts": res["ts"],
    }


@secrets_router.get("/api/v1/secrets/{name}/value")
def api_get_secret_value(
    name: str,
    container=Depends(_get_container),
) -> dict:
    try:
        res = container.secrets_store.get_secret(name, reveal=True)
    except KeyError:
        raise HTTPException(status_code=404, detail="not found")
    return {
        "status": "ok",
        "value": base64.b64encode(res["value"]).decode("utf-8"),
    }


@secrets_router.delete("/api/v1/secrets/{name}")
def api_delete_secret(
    name: str,
    container=Depends(_get_container),
) -> dict:
    container.secrets_store.delete_secret(name, actor="api")
    return {"status": "ok"}


@secrets_router.post("/api/v1/secrets/rotate")
def api_schedule_rotate(
    req: dict = Body(...),
    container=Depends(_get_container),
) -> dict:
    name = req.get("name")
    interval = int(req.get("interval_seconds", 3600))
    policy = req.get("policy", {})
    rid = container.secrets_rotator.schedule_rotation(
        name, interval, policy
    )
    return {"status": "ok", "rotation_id": rid}


@secrets_router.post("/api/v1/secrets/rotate/run")
def api_run_rotate(
    req: dict = Body(...),
    container=Depends(_get_container),
) -> dict:
    rid = req.get("rotation_id")
    if not rid:
        raise HTTPException(status_code=400, detail="missing rotation_id")
    res = container.secrets_rotator.run_rotation(rid)
    return {"status": "ok", "result": res}


@secrets_router.get("/api/v1/secrets/audit")
def api_get_audit(
    container=Depends(_get_container),
) -> dict:
    raw = container.storage.get("secrets:audit") or b"[]"
    arr = json.loads(raw.decode("utf-8")) if raw else []
    return {"status": "ok", "audit": arr}
