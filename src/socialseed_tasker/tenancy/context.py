# src/socialseed_tasker/tenancy/context.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict
from fastapi import Request

@dataclass
class TenantContext:
    tenant_id: str
    config: Dict

def get_current_tenant(request: Optional[Request] = None) -> Optional[TenantContext]:
    if request is None:
        return None
    return getattr(request.state, "tenant", None)
