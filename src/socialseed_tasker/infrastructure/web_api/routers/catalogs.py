"""API router for the seeded PostgreSQL catalogs (issue #572).

``GET /skills`` and ``GET /tools`` expose the catalogs that #558 seeds and
the user/agent forms upsert into (#559/#560/#566), so the frontend pickers
have a single source of truth: the divergent ``AGENT_TOOLS`` vs
``EditAgentModal`` tool lists collapse onto the canonical snake_case slugs.
Skills accept free values (upserted on save); tools are validated against
the same catalog with 422 (#564).
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from socialseed_tasker.auth.user_store import PostgresUserStore
from socialseed_tasker.config.storage import get_database_url
from socialseed_tasker.infrastructure.web_api.schemas import (
    APIResponse,
    Meta,
    SkillCatalogItem,
    ToolCatalogItem,
)

catalogs_router = APIRouter()


def _pg_store() -> PostgresUserStore:
    """PostgreSQL store for the catalog reads (issue #572)."""
    database_url = get_database_url()
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL not configured: TASKER_DATABASE_URL is not set",
        )
    return PostgresUserStore(database_url)


@catalogs_router.get(
    "/skills",
    response_model=APIResponse[list[SkillCatalogItem]],
    summary="List skills catalog",
    description="List the seeded+upserted skills catalog ordered by name (issue #572).",
)
def list_skills() -> APIResponse[list[SkillCatalogItem]]:
    """List the skills catalog (PostgreSQL, issue #572)."""
    items = _pg_store().list_skills()
    return APIResponse(
        data=[SkillCatalogItem(id=item["id"], name=item["name"]) for item in items],
        meta=Meta(request_id=None),
    )


@catalogs_router.get(
    "/tools",
    response_model=APIResponse[list[ToolCatalogItem]],
    summary="List tools catalog",
    description="List the canonical agent tools catalog ordered by name (issue #572).",
)
def list_tools() -> APIResponse[list[ToolCatalogItem]]:
    """List the tools catalog (PostgreSQL, issue #572)."""
    items = _pg_store().list_tools()
    return APIResponse(
        data=[
            ToolCatalogItem(id=item["id"], name=item["name"], description=item.get("description"))
            for item in items
        ],
        meta=Meta(request_id=None),
    )
