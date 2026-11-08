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

import psycopg
from fastapi import APIRouter, HTTPException

from socialseed_tasker.auth.user_store import (
    TOOLS_SEED,
    PostgresAgentPermissionPolicyStore,
    PostgresAgentProfileStore,
)
from socialseed_tasker.config.agent_models import (
    AgentModelConfigurationError,
    validate_agent_model,
)
from socialseed_tasker.config.storage import get_database_url
from socialseed_tasker.domain.agent_limits import parse_agent_limits
from socialseed_tasker.domain.agent_policy import resolve_effective_permissions
from socialseed_tasker.infrastructure.web_api.schemas import (
    AgentEffectivePermissionsResponse,
    AgentPermissionLimitsResponse,
    AgentPermissionPolicyCreate,
    AgentPermissionPolicyResponse,
    AgentPermissionSetResponse,
    AgentPermissionSourceResponse,
    AgentPolicyScope,
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


def _permission_policy_store() -> PostgresAgentPermissionPolicyStore:
    """PostgreSQL store for organization/project permission ceilings (#613)."""
    database_url = get_database_url()
    if not database_url:
        raise HTTPException(
            status_code=503,
            detail="PostgreSQL not configured: TASKER_DATABASE_URL is not set",
        )
    return PostgresAgentPermissionPolicyStore(database_url)


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
        read_access=list(profile.get("read_access") or []),
        write_access=list(profile.get("write_access") or []),
        propose_access=list(profile.get("propose_access") or []),
        apply_access=list(profile.get("apply_access") or []),
        limits=profile.get("limits"),
        enabled=bool(profile.get("enabled", True)),
        skills=list(profile.get("skills") or []),
        created_at=profile.get("created_at"),
        last_used_at=profile.get("last_used_at"),
    )


def _normalize_limits(raw: dict[str, Any] | None) -> dict[str, Any] | None:
    """Validate and canonicalize a typed limits document (#617)."""
    if raw is None:
        return None
    try:
        return parse_agent_limits(raw).as_dict()
    except ValueError as exc:
        _map_store_error(exc)
        raise


def _map_store_error(exc: ValueError) -> None:
    """Map store ValueErrors onto HTTP status codes."""
    message = str(exc)
    if message.startswith("tool:"):
        raise HTTPException(status_code=422, detail=f"unknown tool: {message.split(':', 1)[1]}") from exc
    if message.startswith("resource:"):
        raise HTTPException(
            status_code=422, detail=f"unknown resource: {message.split(':', 1)[1]}"
        ) from exc
    if message.startswith("scope:"):
        raise HTTPException(
            status_code=422, detail=f"unknown policy scope: {message.split(':', 1)[1]}"
        ) from exc
    if message.startswith("scope_id:"):
        raise HTTPException(status_code=422, detail="policy scope_id is required") from exc
    if message in {
        "limits",
        "max_tokens_per_run",
        "max_cost_usd_per_run",
        "max_duration_seconds",
        "max_tool_calls_per_run",
        "max_risk",
    } or message.startswith("max_"):
        raise HTTPException(
            status_code=422, detail=f"invalid agent limit: {message.split(':', 1)[0]}"
        ) from exc
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
    try:
        validate_agent_model(body.model, body.temperature)
    except AgentModelConfigurationError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

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
            read_access=body.read_access,
            write_access=body.write_access,
            propose_access=body.propose_access,
            apply_access=body.apply_access,
            limits=_normalize_limits(body.limits),
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
    if body.model is not None or body.temperature is not None:
        existing_profile = store.get_profile(agent_id)
        if not existing_profile:
            raise HTTPException(status_code=404, detail="Agent profile not found")
        try:
            effective_model = (
                body.model if body.model is not None else existing_profile.get("model")
            )
            effective_temperature = (
                body.temperature
                if body.temperature is not None
                else existing_profile.get("temperature")
            )
            validate_agent_model(effective_model, effective_temperature)
        except AgentModelConfigurationError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

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
            read_access=body.read_access,
            write_access=body.write_access,
            propose_access=body.propose_access,
            apply_access=body.apply_access,
            limits=_normalize_limits(body.limits),
            skills=body.skills,
            enabled=body.enabled,
            last_used_at=body.last_used_at,
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

def _policy_to_response(policy: dict[str, Any]) -> AgentPermissionPolicyResponse:
    """Compose the API response for one permission policy (#613)."""
    return AgentPermissionPolicyResponse(
        id=str(policy["id"]),
        name=str(policy["name"]),
        scope_type=policy["scope_type"],
        scope_id=str(policy["scope_id"]),
        tools=policy.get("tools"),
        read_access=policy.get("read_access"),
        propose_access=policy.get("propose_access"),
        apply_access=policy.get("apply_access"),
        limits=policy.get("limits"),
        is_active=bool(policy.get("is_active", True)),
        created_at=policy.get("created_at"),
    )


def _permission_set_response(values: dict[str, list[str]]) -> AgentPermissionSetResponse:
    return AgentPermissionSetResponse(
        tools=values["tools"],
        read_access=values["read_access"],
        propose_access=values["propose_access"],
        apply_access=values["apply_access"],
    )


def _permission_limits_response(
    values: dict[str, list[str] | None],
) -> AgentPermissionLimitsResponse:
    return AgentPermissionLimitsResponse(
        tools=values["tools"],
        read_access=values["read_access"],
        propose_access=values["propose_access"],
        apply_access=values["apply_access"],
    )


@agent_profiles_router.get(
    "/agents/permission-policies",
    response_model=APIResponse[list[AgentPermissionPolicyResponse]],
    summary="List agent permission policies",
    description="List organization/project permission ceilings (issue #613).",
)
def list_agent_permission_policies(
    scope_type: AgentPolicyScope | None = None,
    scope_id: str | None = None,
    is_active: bool | None = None,
) -> APIResponse[list[AgentPermissionPolicyResponse]]:
    """List stored permission ceilings, optionally filtered by scope."""
    try:
        policies = _permission_policy_store().list_policies(
            scope_type=scope_type, scope_id=scope_id, is_active=is_active
        )
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="permission policy source unavailable") from exc
    return APIResponse(
        data=[_policy_to_response(policy) for policy in policies],
        meta=Meta(request_id=None),
    )


@agent_profiles_router.post(
    "/agents/permission-policies",
    response_model=APIResponse[AgentPermissionPolicyResponse],
    status_code=201,
    summary="Create an agent permission policy",
    description="Create an organization/project ceiling; omitted capabilities are unrestricted (#613).",
)
def create_agent_permission_policy(
    body: AgentPermissionPolicyCreate,
) -> APIResponse[AgentPermissionPolicyResponse]:
    """Create a permission ceiling; policies can only restrict profiles."""
    try:
        policy = _permission_policy_store().create_policy(
            name=body.name,
            scope_type=body.scope_type,
            scope_id=body.scope_id,
            tools=body.tools,
            read_access=body.read_access,
            propose_access=body.propose_access,
            apply_access=body.apply_access,
            limits=_normalize_limits(body.limits),
            is_active=body.is_active,
        )
    except ValueError as exc:
        _map_store_error(exc)
        raise
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="permission policy source unavailable") from exc
    return APIResponse(data=_policy_to_response(policy), meta=Meta(request_id=None))


@agent_profiles_router.delete(
    "/agents/permission-policies/{policy_id}",
    response_model=APIResponse[bool],
    summary="Delete an agent permission policy",
    description="Delete a permission ceiling; 404 when it does not exist (issue #613).",
)
def delete_agent_permission_policy(policy_id: str) -> APIResponse[bool]:
    """Delete one permission ceiling."""
    try:
        deleted = _permission_policy_store().delete_policy(policy_id)
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="permission policy source unavailable") from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent permission policy not found")
    return APIResponse(data=True, meta=Meta(request_id=None))


@agent_profiles_router.get(
    "/agents/profiles/{agent_id}/permissions",
    response_model=APIResponse[AgentEffectivePermissionsResponse],
    summary="Get effective agent permissions",
    description=(
        "Intersect explicit profile capabilities with organization/project ceilings "
        "for the given context; unresolved policies deny everything (issue #613)."
    ),
)
def get_effective_agent_permissions(
    agent_id: str,
    organization_id: str | None = None,
    project_id: str | None = None,
) -> APIResponse[AgentEffectivePermissionsResponse]:
    """Resolve explicit, inherited and effective permissions for one agent."""
    profile = _pg_store().get_profile(agent_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    try:
        policies = _permission_policy_store().list_for_context(
            organization_id=organization_id, project_id=project_id
        )
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="permission policy source unavailable") from exc
    resolved = resolve_effective_permissions(
        explicit={field: profile.get(field) or [] for field in (
            "tools",
            "read_access",
            "propose_access",
            "apply_access",
        )},
        enabled=bool(profile.get("enabled", True)),
        policies=policies,
        known_tools=[slug for slug, _, _ in TOOLS_SEED],
    )
    return APIResponse(
        data=AgentEffectivePermissionsResponse(
            agent_id=agent_id,
            status=resolved.status,
            profile_enabled=resolved.profile_enabled,
            explicit=_permission_set_response(resolved.explicit.as_dict()),
            inherited=_permission_limits_response(resolved.inherited.as_dict()),
            effective=_permission_set_response(resolved.effective.as_dict()),
            sources=[
                AgentPermissionSourceResponse(
                    id=source.id,
                    name=source.name,
                    scope=source.scope,
                    scope_id=source.scope_id,
                )
                for source in resolved.sources
            ],
            errors=list(resolved.errors),
        ),
        meta=Meta(request_id=None),
    )
