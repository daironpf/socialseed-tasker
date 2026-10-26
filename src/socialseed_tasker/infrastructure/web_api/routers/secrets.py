from __future__ import annotations

import base64
import json
import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from socialseed_tasker.auth.oauth import SESSION_COOKIE_NAME
from socialseed_tasker.auth.permissions import require_permission
from socialseed_tasker.cli.wiring import build_default_container
from socialseed_tasker.infrastructure.web_api.schemas import (
    APIResponse,
    Meta,
    SecretMetadataResponse,
    SecretPutRequest,
    SecretRotateRunRequest,
    SecretRotateScheduleRequest,
)

logger = logging.getLogger(__name__)

secrets_router = APIRouter()


def _get_container() -> Any:
    return build_default_container()


def _meta() -> Meta:
    return Meta(request_id=None)


def _require_secret_admin(request: Request, container: Any) -> None:
    authorization = request.headers.get("authorization", "")
    has_bearer = authorization.lower().startswith("bearer ") and bool(
        authorization[7:].strip()
    )
    has_api_key = bool(request.headers.get("x-api-key", "").strip())
    has_session = bool(request.cookies.get(SESSION_COOKIE_NAME))
    if not (has_bearer or has_api_key or has_session):
        raise HTTPException(status_code=401, detail="unauthorized")
    require_permission(request, "admin", container)


def _check_permission(
    container: Any, user_id: str | None, permission: str
) -> None:
    if not user_id:
        raise HTTPException(status_code=403, detail="forbidden")
    if not container.rbac.has_permission(user_id, permission):
        raise HTTPException(status_code=403, detail="forbidden")


@secrets_router.post("/api/v1/secrets")
def api_put_secret(
    req: SecretPutRequest,
    container: Any = Depends(_get_container),
) -> APIResponse[dict[str, Any]]:
    name = req.name
    val_b64 = req.value
    meta = req.metadata
    if not name or not val_b64:
        raise HTTPException(status_code=400, detail="missing name or value")
    val = base64.b64decode(val_b64.encode("utf-8"))
    container.secrets_store.put_secret(
        name, val, metadata=meta, actor="api"
    )
    return APIResponse(data={"name": name}, meta=_meta())


@secrets_router.get(
    "/api/v1/secrets",
    response_model=APIResponse[list[SecretMetadataResponse]],
    summary="List secret metadata",
    description="Return secret names and metadata without revealing secret values.",
)
def api_list_secrets(
    request: Request,
    container: Any = Depends(_get_container),
) -> APIResponse[list[SecretMetadataResponse]]:
    _require_secret_admin(request, container)
    secrets: list[SecretMetadataResponse] = []
    for name in container.secrets_store.list_secrets():
        secret = container.secrets_store.get_secret(name, reveal=False)
        secrets.append(
            SecretMetadataResponse(
                name=name,
                metadata=secret["metadata"],
                ts=secret["ts"],
            )
        )
    return APIResponse(data=secrets, meta=_meta())


@secrets_router.get("/api/v1/secrets/audit")
def api_get_audit(
    container: Any = Depends(_get_container),
) -> APIResponse[dict[str, Any]]:
    raw = container.storage.get("secrets:audit") or b"[]"
    arr = json.loads(raw.decode("utf-8")) if raw else []
    return APIResponse(data={"audit": arr}, meta=_meta())


@secrets_router.get("/api/v1/secrets/{name}")
def api_get_secret_meta(
    name: str,
    container: Any = Depends(_get_container),
) -> APIResponse[dict[str, Any]]:
    try:
        res = container.secrets_store.get_secret(name, reveal=False)
    except (KeyError, ValueError):
        raise HTTPException(status_code=404, detail="not found")
    return APIResponse(
        data={
            "name": name,
            "metadata": res["metadata"],
            "ts": res["ts"],
        },
        meta=_meta(),
    )


@secrets_router.get("/api/v1/secrets/{name}/value")
def api_get_secret_value(
    name: str,
    container: Any = Depends(_get_container),
) -> APIResponse[dict[str, Any]]:
    try:
        res = container.secrets_store.get_secret(name, reveal=True)
    except (KeyError, ValueError):
        raise HTTPException(status_code=404, detail="not found")
    return APIResponse(
        data={
            "name": name,
            "value": base64.b64encode(res["value"]).decode("utf-8"),
        },
        meta=_meta(),
    )


@secrets_router.delete("/api/v1/secrets/{name}")
def api_delete_secret(
    name: str,
    container: Any = Depends(_get_container),
) -> APIResponse[dict[str, Any]]:
    container.secrets_store.delete_secret(name, actor="api")
    return APIResponse(data={"deleted": True, "name": name}, meta=_meta())


@secrets_router.post("/api/v1/secrets/rotate")
def api_schedule_rotate(
    req: SecretRotateScheduleRequest,
    container: Any = Depends(_get_container),
) -> APIResponse[dict[str, Any]]:
    name = req.name
    interval = req.interval_seconds
    policy = req.policy
    rid = container.secrets_rotator.schedule_rotation(
        name, interval, policy
    )
    return APIResponse(data={"rotation_id": rid}, meta=_meta())


@secrets_router.post("/api/v1/secrets/rotate/run")
def api_run_rotate(
    req: SecretRotateRunRequest,
    container: Any = Depends(_get_container),
) -> APIResponse[dict[str, Any]]:
    rid = req.rotation_id
    if not rid:
        raise HTTPException(status_code=400, detail="missing rotation_id")
    res = container.secrets_rotator.run_rotation(rid)
    return APIResponse(data={"rotation_id": rid, "result": res}, meta=_meta())
