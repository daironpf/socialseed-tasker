"""API router for tenant management (admin only).

Authorization goes through the unified permission guard (issue #593): the
same ``require_permission`` policy shared with ``/data-quality`` writes,
accepting static tokens, login JWTs and OAuth session cookies.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from socialseed_tasker.auth.permissions import require_permission

tenants_router = APIRouter()


def _container(request: Request) -> Any:
    container = getattr(request.app.state, "container", None)
    if container is None:
        from socialseed_tasker.cli.wiring import build_default_container
        container = build_default_container()
    return container


@tenants_router.post("/admin/tenants")
def api_create_tenant(req: dict[Any, Any], request: Request) -> Any:
    container = _container(request)
    require_permission(request, "admin", container)
    tid = req.get("id")
    if not isinstance(tid, str) or not tid:
        from fastapi import HTTPException

        raise HTTPException(status_code=422, detail="Tenant id must be a non-empty string")
    cfg = req.get("config", {})
    tenant = container.tenant_store.create_tenant(tid, cfg)
    from socialseed_tasker.tenancy.migrations import ensure_tenant_schema
    ensure_tenant_schema(tid)
    return {"status": "ok", "tenant": tenant}


@tenants_router.get("/admin/tenants")
def api_list_tenants(request: Request) -> Any:
    container = _container(request)
    require_permission(request, "admin", container)
    return {"status": "ok", "tenants": container.tenant_store.list_tenants()}


@tenants_router.get("/admin/tenants/{tenant_id}")
def api_get_tenant(tenant_id: str, request: Request) -> Any:
    container = _container(request)
    require_permission(request, "admin", container)
    t = container.tenant_store.get_tenant(tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="not found")
    return {"status": "ok", "tenant": t}


@tenants_router.delete("/admin/tenants/{tenant_id}")
def api_delete_tenant(tenant_id: str, request: Request) -> Any:
    container = _container(request)
    require_permission(request, "admin", container)
    container.tenant_store.delete_tenant(tenant_id)
    return {"status": "ok"}
