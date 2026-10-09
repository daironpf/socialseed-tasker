"""API router for agent profiles on the dedicated /agents/profiles prefix (issue #564).

Agent identities of the Users view are NOT served by the generic /users
endpoint (humans, last-human guard); they live in their own ``agents_user``
table over the PostgreSQL root. The router is registered in ``app.py``
**before** ``agent.py`` so ``/agents/profiles`` is never swallowed by the
``/agents/{agent_id}`` path parameter. Agent Studio migrates onto this API in
issue #573.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from socialseed_tasker.auth.user_store import PostgresAgentProfileStore
from socialseed_tasker.config.storage import get_database_url
from socialseed_tasker.infrastructure.web_api.schemas import (
    AgentProfileCreate,
    AgentProfileResponse,
    AgentProfileUpdate,
    APIResponse,
    Meta,
)

agent_profiles_router = APIRouter()


def _pg_store() -> PostgresAgentProfileStore:
    """PostgreSQL store for /agents/profiles (issue #564)."""
    database_url = get_database_url()
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL not configured: TASKER_DATABASE_URL is not set",
        )
    return PostgresAgentProfileStore(database_url)


def _profile_to_response(profile: dict[str, Any]) -> AgentProfileResponse:
    """Compose the API response from a composed PostgreSQL profile dict."""
    return AgentProfileResponse(
        id=str(profile["id"]),
        username=profile["username"],
        email=profile.get("email"),
        type="agent",
        avatar=profile.get("avatar"),
        model=profile.get("model"),
        specialization=profile.get("specialization"),
        temperature=profile.get("temperature"),
        system_prompt=profile.get("system_prompt"),
        tools=list(profile.get("tools") or []),
        write_access=list(profile.get("write_access") or []),
        limits=profile.get("limits"),
        enabled=bool(profile.get("enabled", True)),
        skills=list(profile.get("skills") or []),
        created_at=profile.get("created_at"),
        last_used_at=profile.get("last_used_at"),
    )


def _map_store_error(exc: ValueError) -> None:
    """Map store ValueErrors onto HTTP status codes."""
    message = str(exc)
    if message.startswith("tool:"):
        raise HTTPException(status_code=422, detail=f"unknown tool: {message.split(':', 1)[1]}") from exc
    if message == "username":
        raise HTTPException(status_code=409, detail="username already exists") from exc
    raise


@agent_profiles_router.get(
    "/agents/profiles",
    response_model=APIResponse[list[AgentProfileResponse]],
    summary="List agent profiles",
    description="List every agent profile stored in the PostgreSQL root (issue #564).",
)
def list_agent_profiles() -> APIResponse[list[AgentProfileResponse]]:
    """List agent profiles (PostgreSQL, issue #564)."""
    profiles = _pg_store().list_profiles()
    return APIResponse(data=[_profile_to_response(p) for p in profiles], meta=Meta(request_id=None))


@agent_profiles_router.get(
    "/agents/profiles/{agent_id}",
    response_model=APIResponse[AgentProfileResponse],
    summary="Get agent profile by ID",
    description="Get one agent profile by its PostgreSQL uid (issue #564).",
)
def get_agent_profile(agent_id: str) -> APIResponse[AgentProfileResponse]:
    """Get an agent profile by id (issue #564)."""
    profile = _pg_store().get_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    return APIResponse(data=_profile_to_response(profile), meta=Meta(request_id=None))


@agent_profiles_router.post(
    "/agents/profiles",
    response_model=APIResponse[AgentProfileResponse],
    status_code=201,
    summary="Create agent profile",
    description="Create an agent identity (users + agents_user) with a PG-generated uid (issue #564).",
)
def create_agent_profile(body: AgentProfileCreate) -> APIResponse[AgentProfileResponse]:
    """Create an agent profile across ``users``/``agents_user``/``user_skills`` (#564).

    The agent gets no credential and no RBAC role: it cannot log in. Unknown
    ``tools`` slugs are rejected with 422 before anything is written.
    """
    store = _pg_store()
    try:
        uid = store.create_profile(
            username=body.username,
            email=body.email,
            avatar=body.avatar,
            model=body.model,
            specialization=body.specialization,
            temperature=body.temperature,
            system_prompt=body.system_prompt,
            tools=body.tools,
            write_access=body.write_access,
            limits=body.limits,
            skills=body.skills,
            enabled=body.enabled,
        )
    except ValueError as exc:
        _map_store_error(exc)
        raise
    profile = store.get_profile(uid)
    if not profile:
        raise HTTPException(status_code=500, detail="created agent profile could not be read back")
    return APIResponse(data=_profile_to_response(profile), meta=Meta(request_id=None))


@agent_profiles_router.put(
    "/agents/profiles/{agent_id}",
    response_model=APIResponse[AgentProfileResponse],
    summary="Update agent profile",
    description="Partially update an agent profile; None keeps the stored value (issue #564).",
)
def update_agent_profile(agent_id: str, body: AgentProfileUpdate) -> APIResponse[AgentProfileResponse]:
    """Update an agent profile (issue #564): 404 sin fila, 409 username duplicado."""
    store = _pg_store()
    try:
        store.update_profile(
            agent_id,
            username=body.username,
            email=body.email,
            avatar=body.avatar,
            model=body.model,
            specialization=body.specialization,
            temperature=body.temperature,
            system_prompt=body.system_prompt,
            tools=body.tools,
            write_access=body.write_access,
            limits=body.limits,
            skills=body.skills,
            enabled=body.enabled,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Agent profile not found") from exc
    except ValueError as exc:
        _map_store_error(exc)
        raise
    profile = store.get_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    return APIResponse(data=_profile_to_response(profile), meta=Meta(request_id=None))


@agent_profiles_router.delete(
    "/agents/profiles/{agent_id}",
    summary="Delete agent profile",
    description="Cascade-delete the agent identity; no last-human guard applies (issue #564).",
)
def delete_agent_profile(agent_id: str) -> APIResponse[bool]:
    """Delete an agent profile; ``users`` cascade cleans ``agents_user``/``user_skills``."""
    deleted = _pg_store().delete_profile(agent_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    return APIResponse(data=True, meta=Meta(request_id=None))
