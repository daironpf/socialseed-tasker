"""API router for tenant management (admin only)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from socialseed_tasker.auth.auth import load_auth_provider

tenants_router = APIRouter()


def _resolve_admin_user(request: Request) -> str | None:
    auth = request.headers.get("authorization", "")
    user_id = None
    if auth.lower().startswith("bearer "):
        user_id = load_auth_provider().verify_token(auth.split(" ", 1)[1])
    if not user_id:
        from socialseed_tasker.auth.oauth import SESSION_COOKIE_NAME
        sid = request.cookies.get(SESSION_COOKIE_NAME)
        if sid:
            session_store = getattr(request.app.state, "session_store", None)
            if session_store:
                session = session_store.get(sid)
                if session:
                    claims = session.get("claims", {})
                    user_id = claims.get("preferred_username") or claims.get("sub")
    return user_id


@tenants_router.post("/admin/tenants")
def api_create_tenant(req: dict, request: Request):
    user_id = _resolve_admin_user(request)
    container = getattr(request.app.state, "container", None)
    if container is None:
        from socialseed_tasker.cli.wiring import build_default_container
        container = build_default_container()
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    tid = req.get("id")
    cfg = req.get("config", {})
    tenant = container.tenant_store.create_tenant(tid, cfg)
    from socialseed_tasker.tenancy.migrations import ensure_tenant_schema
    ensure_tenant_schema(tid)
    return {"status": "ok", "tenant": tenant}


@tenants_router.get("/admin/tenants")
def api_list_tenants(request: Request):
    user_id = _resolve_admin_user(request)
    container = getattr(request.app.state, "container", None)
    if container is None:
        from socialseed_tasker.cli.wiring import build_default_container
        container = build_default_container()
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    return {"status": "ok", "tenants": container.tenant_store.list_tenants()}


@tenants_router.get("/admin/tenants/{tenant_id}")
def api_get_tenant(tenant_id: str, request: Request):
    user_id = _resolve_admin_user(request)
    container = getattr(request.app.state, "container", None)
    if container is None:
        from socialseed_tasker.cli.wiring import build_default_container
        container = build_default_container()
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    t = container.tenant_store.get_tenant(tenant_id)
    if not t:
        raise HTTPException(status_code=404, detail="not found")
    return {"status": "ok", "tenant": t}


@tenants_router.delete("/admin/tenants/{tenant_id}")
def api_delete_tenant(tenant_id: str, request: Request):
    user_id = _resolve_admin_user(request)
    container = getattr(request.app.state, "container", None)
    if container is None:
        from socialseed_tasker.cli.wiring import build_default_container
        container = build_default_container()
    if not container.rbac.has_permission(user_id, "admin"):
        raise HTTPException(status_code=403, detail="forbidden")
    container.tenant_store.delete_tenant(tenant_id)
    return {"status": "ok"}
