"""API router for human approvals bound to concrete agent actions (#616).

Agents request and consume approvals with a run-scoped execution credential
(``aet_...``) issued by ``POST /issues/{id}/agent/start``. Humans list, decide
and revoke approvals through the same unified permission guard used by the
other admin surfaces, so an agent token can never decide its own request.
"""

from __future__ import annotations

import logging
from typing import Annotated, Any

import psycopg
from fastapi import APIRouter, Depends, HTTPException, Query, Request

from socialseed_tasker.application.actions import TaskRepositoryInterface
from socialseed_tasker.application.agent_approvals import AgentApprovalService
from socialseed_tasker.application.agent_limits import AgentLimitError, AgentLimitGuard
from socialseed_tasker.auth.permissions import require_permission
from socialseed_tasker.auth.tokens import verify_agent_execution_token
from socialseed_tasker.infrastructure.web_api.agent_approvals import (
    create_agent_approval_service,
)
from socialseed_tasker.infrastructure.web_api.agent_authorization import (
    create_agent_action_authorizer,
    create_agent_profile_store,
    resolve_component_project_id,
)
from socialseed_tasker.infrastructure.web_api.routers.helpers import (
    get_repository_provider as get_repo,
)
from socialseed_tasker.infrastructure.web_api.schemas import (
    AgentApprovalDecisionRequest,
    AgentApprovalExecutionRequest,
    AgentApprovalRequestCreate,
    AgentApprovalResponse,
    APIResponse,
    Meta,
)

logger = logging.getLogger(__name__)

agent_approvals_router = APIRouter()


def _container(request: Request) -> Any:
    container = getattr(request.app.state, "container", None)
    if container is None:
        from socialseed_tasker.cli.wiring import build_default_container

        container = build_default_container()
    return container


def _as_response(row: dict[str, Any]) -> AgentApprovalResponse:
    """Convert a stored row into the public response model."""
    return AgentApprovalResponse(**_approval_fields(row))


def _approval_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {key: row.get(key) for key in AgentApprovalResponse.model_fields if key in row}


def _wrap(row: dict[str, Any]) -> APIResponse[AgentApprovalResponse]:
    return APIResponse(data=_as_response(row), meta=Meta(request_id=None))


def _human_approver(request: Request, container: Any) -> str:
    """Resolve an authenticated human with the admin permission.

    Agent profiles live in ``agents_user`` and are explicitly rejected even if
    a misconfigured grant gives them the admin permission: an agent must never
    approve its own action.
    """
    identity = require_permission(request, "admin", container)
    if not identity:
        raise HTTPException(status_code=403, detail="A human approver is required")
    try:
        profile = create_agent_profile_store().get_profile(identity)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Agent profile store unavailable") from exc
    if profile is not None:
        raise HTTPException(status_code=403, detail="Agent profiles cannot decide approvals")
    return identity


def _execution_token(request: Request) -> str | None:
    header = request.headers.get("X-Agent-Execution-Token")
    if header:
        return header
    authorization = request.headers.get("Authorization", "")
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return None


def _execution_claims(request: Request) -> dict[str, Any]:
    token = _execution_token(request)
    claims = verify_agent_execution_token(token or "")
    if claims is None:
        raise HTTPException(
            status_code=401,
            detail="A valid agent execution credential is required",
        )
    return claims


def _execution_context(
    *,
    request: Request,
    repository: TaskRepositoryInterface,
) -> dict[str, Any]:
    """Validate the run, issue and project claims of an execution token."""
    claims = _execution_claims(request)
    agent_id = str(claims["sub"])
    run_id = str(claims["run_id"])
    issue_id = str(claims["issue_id"])
    project_id = str(claims["project_id"])

    try:
        profiles = create_agent_profile_store()
        run = profiles.get_run(run_id)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Agent run store unavailable") from exc

    if (
        run is None
        or run.get("status") != "running"
        or str(run.get("agent_id")) != agent_id
        or str(run.get("issue_id")) != issue_id
    ):
        raise HTTPException(status_code=403, detail="Agent run is not active for this approval")

    issue = repository.get_issue(issue_id)
    if issue is None:
        raise HTTPException(status_code=403, detail="Execution issue no longer exists")
    component = repository.get_component(str(issue.component_id))
    resolved_project = resolve_component_project_id(component, repository) if component is not None else None
    if resolved_project != project_id:
        raise HTTPException(status_code=403, detail="Execution project context changed")

    return {
        "claims": claims,
        "agent_id": agent_id,
        "run_id": run_id,
        "issue_id": issue_id,
        "project_id": project_id,
    }


def _limit_guard() -> AgentLimitGuard:
    return AgentLimitGuard(create_agent_profile_store())


def _enforce_limits(
    *,
    context: dict[str, Any],
    effective_limits: Any,
    consume_action: bool,
) -> None:
    """Reject a new action when the run already reached a server-measured limit."""
    guard = _limit_guard()
    try:
        if consume_action:
            guard.consume_tool_call(context["run_id"], effective_limits)
        else:
            guard.check(context["run_id"], effective_limits)
    except LookupError as exc:
        raise HTTPException(status_code=403, detail="Agent run is not active") from exc
    except AgentLimitError:
        # The guard already stopped the run and logged the reached limit; the
        # application error handler turns this into a 409 with its metadata.
        raise


def _authorize_action(
    *,
    context: dict[str, Any],
    action: str,
    tool: str | None,
    resource_scope: str,
) -> Any:
    try:
        authorizer = create_agent_action_authorizer()
        decision = authorizer.authorize(
            agent_id=context["agent_id"],
            tool=tool,
            action=action,
            resource_scope=resource_scope,
            project_id=context["project_id"],
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except psycopg.Error as exc:
        raise HTTPException(status_code=503, detail="Agent authorization source unavailable") from exc
    if not decision.allowed:
        logger.warning(
            "Agent approval denied: agent=%s action=%s scope=%s reason=%s",
            context["agent_id"],
            action,
            resource_scope,
            decision.reason,
        )
    return decision


def _service() -> AgentApprovalService:
    return create_agent_approval_service()


@agent_approvals_router.post(
    "/agent-approvals",
    response_model=APIResponse[AgentApprovalResponse],
    summary="Request human approval for one agent action",
    description=(
        "Agent-only endpoint. The approval is bound to the execution token's "
        "run, issue and project plus the exact action/effect fingerprint."
    ),
    responses={
        401: {"description": "Missing or invalid execution credential"},
        403: {"description": "Run, project or action not authorized"},
    },
)
def request_agent_approval(
    body: AgentApprovalRequestCreate,
    request: Request,
    repository: Annotated[TaskRepositoryInterface, Depends(get_repo)],
) -> APIResponse[AgentApprovalResponse]:
    context = _execution_context(request=request, repository=repository)
    decision = _authorize_action(
        context=context,
        action=body.action,
        tool=body.tool,
        resource_scope=body.resource_scope,
    )
    if not decision.allowed:
        raise HTTPException(
            status_code=403,
            detail="Agent is not authorized for this action",
        )
    _enforce_limits(
        context=context,
        effective_limits=decision.effective_limits,
        consume_action=False,
    )
    row = _service().request_approval(
        run_id=context["run_id"],
        agent_id=context["agent_id"],
        issue_id=context["issue_id"],
        project_id=context["project_id"],
        action=body.action,
        tool=body.tool,
        resource_scope=body.resource_scope,
        target=body.target,
        expected_effect=body.expected_effect,
        action_payload=body.action_payload,
        expires_in_seconds=body.expires_in_seconds,
        request_metadata=body.metadata.model_dump(),
    )
    return _wrap(row)


@agent_approvals_router.get(
    "/agent-approvals",
    response_model=APIResponse[list[AgentApprovalResponse]],
    summary="List agent approvals",
    description="Human-only inbox backed by persisted server state.",
)
def list_agent_approvals(
    request: Request,
    status: Annotated[str | None, Query(description="pending|approved|rejected|revoked|expired")] = None,
    issue_id: Annotated[str | None, Query()] = None,
    agent_id: Annotated[str | None, Query()] = None,
    project_id: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> APIResponse[list[AgentApprovalResponse]]:
    _human_approver(request, _container(request))
    rows = _service().list_approvals(
        status=status,
        issue_id=issue_id,
        agent_id=agent_id,
        project_id=project_id,
        limit=limit,
    )
    return APIResponse(
        data=[_as_response(row) for row in rows],
        meta=Meta(request_id=None),
    )


@agent_approvals_router.get(
    "/agent-approvals/{approval_id}",
    response_model=APIResponse[AgentApprovalResponse],
    summary="Get one agent approval",
)
def get_agent_approval(approval_id: str, request: Request) -> APIResponse[AgentApprovalResponse]:
    _human_approver(request, _container(request))
    row = _service().get_approval(approval_id)
    return _wrap(row)


def _decision(
    approval_id: str,
    request: Request,
    body: AgentApprovalDecisionRequest | None,
    *,
    action: str,
) -> APIResponse[AgentApprovalResponse]:
    actor_id = _human_approver(request, _container(request))
    service = _service()
    current = service.get_approval(approval_id)
    if str(current.get("agent_id")) == actor_id:
        raise HTTPException(status_code=403, detail="An agent cannot approve its own action")
    feedback = body.feedback if body is not None else None
    if action == "approve":
        row = service.approve(approval_id, actor_id=actor_id, feedback=feedback)
    elif action == "reject":
        row = service.reject(approval_id, actor_id=actor_id, feedback=feedback)
    else:
        row = service.revoke(approval_id, actor_id=actor_id, feedback=feedback)
    return _wrap(row)


@agent_approvals_router.post(
    "/agent-approvals/{approval_id}/approve",
    response_model=APIResponse[AgentApprovalResponse],
    summary="Approve one agent action",
)
def approve_agent_action(
    approval_id: str,
    request: Request,
    body: AgentApprovalDecisionRequest | None = None,
) -> APIResponse[AgentApprovalResponse]:
    return _decision(approval_id, request, body, action="approve")


@agent_approvals_router.post(
    "/agent-approvals/{approval_id}/reject",
    response_model=APIResponse[AgentApprovalResponse],
    summary="Reject one agent action",
)
def reject_agent_action(
    approval_id: str,
    request: Request,
    body: AgentApprovalDecisionRequest | None = None,
) -> APIResponse[AgentApprovalResponse]:
    return _decision(approval_id, request, body, action="reject")


@agent_approvals_router.post(
    "/agent-approvals/{approval_id}/revoke",
    response_model=APIResponse[AgentApprovalResponse],
    summary="Revoke a pending or approved agent action",
)
def revoke_agent_action(
    approval_id: str,
    request: Request,
    body: AgentApprovalDecisionRequest | None = None,
) -> APIResponse[AgentApprovalResponse]:
    return _decision(approval_id, request, body, action="revoke")


@agent_approvals_router.post(
    "/agent-approvals/{approval_id}/execute",
    response_model=APIResponse[AgentApprovalResponse],
    summary="Consume an approval to execute the exact approved action",
    description=(
        "Agent-only one-shot gate. It revalidates run, actor, deadline, action "
        "fingerprint and current authorization before setting executed_at."
    ),
    responses={
        401: {"description": "Missing or invalid execution credential"},
        403: {"description": "Run, actor or authorization mismatch"},
        409: {"description": "Approval is no longer executable or was already used"},
    },
)
def execute_agent_action(
    approval_id: str,
    body: AgentApprovalExecutionRequest,
    request: Request,
    repository: Annotated[TaskRepositoryInterface, Depends(get_repo)],
) -> APIResponse[AgentApprovalResponse]:
    context = _execution_context(request=request, repository=repository)
    decision = _authorize_action(
        context=context,
        action=body.action,
        tool=body.tool,
        resource_scope=body.resource_scope,
    )
    if decision.allowed:
        # Executing consumes one action from the run's step budget; when the
        # limit is already reached the run is stopped and no approval is used.
        _enforce_limits(
            context=context,
            effective_limits=decision.effective_limits,
            consume_action=True,
        )
    row = _service().execute(
        approval_id,
        run_id=context["run_id"],
        agent_id=context["agent_id"],
        action=body.action,
        tool=body.tool,
        resource_scope=body.resource_scope,
        target=body.target,
        expected_effect=body.expected_effect,
        action_payload=body.action_payload,
        authorization_allowed=decision.allowed,
    )
    return _wrap(row)
