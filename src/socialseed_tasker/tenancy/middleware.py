# src/socialseed_tasker/tenancy/middleware.py
from __future__ import annotations
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from socialseed_tasker.tenancy.context import TenantContext

class TenantMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, container):
        super().__init__(app)
        self.container = container

    async def dispatch(self, request: Request, call_next):
        tenant_id = None
        tenant_id = request.headers.get("x-tenant-id")
        if not tenant_id:
            host = request.headers.get("host", "")
            if host and "." in host:
                sub = host.split(".")[0]
                if sub and sub != "localhost":
                    tenant_id = sub
        if not tenant_id:
            auth = request.headers.get("authorization", "")
            if auth.lower().startswith("bearer "):
                token = auth.split(" ", 1)[1]
                token_map = getattr(self.container, "tenancy_token_map", {})
                tenant_id = token_map.get(token)
        tenant_ctx = None
        if tenant_id:
            tenant = self.container.tenant_store.get_tenant(tenant_id)
            if tenant:
                tenant_ctx = TenantContext(tenant_id=tenant_id, config=tenant.get("config", {}))
        request.state.tenant = tenant_ctx
        return await call_next(request)
