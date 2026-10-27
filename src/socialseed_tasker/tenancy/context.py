# src/socialseed_tasker/tenancy/context.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Request


@dataclass
class TenantContext:
    tenant_id: str
    config: dict[Any, Any]

def get_current_tenant(request: Request | None = None) -> TenantContext | None:
    if request is None:
        return None
    return getattr(request.state, "tenant", None)
