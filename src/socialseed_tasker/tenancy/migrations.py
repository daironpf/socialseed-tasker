# src/socialseed_tasker/tenancy/migrations.py
from __future__ import annotations
from typing import Callable, List

def ensure_tenant_schema(tenant_id: str) -> None:
    from socialseed_tasker.cli.wiring import build_default_container
    container = build_default_container()
    if hasattr(container.issue_repo, "ensure_tenant"):
        container.issue_repo.ensure_tenant(tenant_id)
    if hasattr(container.graph_repo, "ensure_tenant"):
        container.graph_repo.ensure_tenant(tenant_id)

def run_migrations(tenant_id: str, migrations: List[Callable[[object], None]]) -> None:
    from socialseed_tasker.cli.wiring import build_default_container
    container = build_default_container()
    for m in migrations:
        m(container)
