"""API route definitions for issues, dependencies, components, and analysis.

All routes delegate to core actions - no business logic lives here.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, Query, Request  # noqa: B008

logger = logging.getLogger(__name__)

from socialseed_tasker.core.project_analysis.analyzer import (
    ComponentImpactAnalysis,
    ImpactAnalysis,
    RootCauseAnalyzer,
    TestFailure,
)
from socialseed_tasker.core.task_management.actions import (
    ComponentNotFoundError,
    IssueNotFoundError,
    PolicyViolationError,
    TaskRepositoryInterface,
    add_dependency_action,
    close_issue_action,
    create_issue_action,
    get_blocked_issues_action,
    get_dependency_chain_action,
    get_workable_issues_action,
    remove_dependency_action,
    reset_data_action,
)
from socialseed_tasker.core.task_management.entities import Component, Issue, IssueStatus
from socialseed_tasker.entrypoints.web_api.schemas import (
    APIResponse,
    BulkDependencyRequest,
    BulkDependencyResponse,
    CausalLinkResponse,
    ComponentCreateRequest,
    ComponentImpactAnalysisResponse,
    ComponentImpactIssueSummary,
    ComponentResponse,
    ConstraintLoadResponse,
    ConstraintResponse,
    ConstraintValidationResponse,
    ConstraintViolationResponse,
    DependencyGraphResponse,
    DependencyRequest,
    DependencyResponse,
    ImpactAnalysisResponse,
    ImpactIssueSummary,
    IssueCreateRequest,
    IssueResponse,
    IssueUpdateRequest,
    ManifestFilesRequest,
    ManifestNotesRequest,
    ManifestResponse,
    ManifestTodoRequest,
    Meta,
    PaginatedResponse,
    PaginationMeta,
    ProjectSummaryResponse,
    ReasoningLogEntryRequest,
    ReasoningLogEntryResponse,
    AgentStartRequest,
    AgentStatusResponse,
    PolicyValidationRequest,
    PolicyValidationResponse,
    PolicyViolationResponse,
    PolicyCreateRequest,
    PolicyResponse,
    TestFailureRequest,
    TestFailureWebhookRequest,
    TestFailureWebhookResponse,
    AgentRegisterRequest,
    AgentUpdateRequest,
    AgentResponse,
    GitHubWebhookLogResponse,
    GitHubWebhookTestResponse,
)

if TYPE_CHECKING:
    pass


class RepositoryDependency:
    """FastAPI dependency that provides the task repository from app state."""

    def __call__(self, request: Request) -> TaskRepositoryInterface:
        return request.app.state.repository


get_repo = RepositoryDependency()


def _issue_to_response(issue: Issue) -> IssueResponse:
    """Convert a domain Issue to an API response model."""
    return IssueResponse(
        id=str(issue.id),
        title=issue.title,
        description=issue.description,
        status=issue.status.value,
        priority=issue.priority.value,
        component_id=str(issue.component_id),
        labels=issue.labels,
        dependencies=[str(d) for d in issue.dependencies],
        blocks=[str(b) for b in issue.blocks],
        affects=[str(a) for a in issue.affects],
        created_at=issue.created_at,
        updated_at=issue.updated_at,
        closed_at=issue.closed_at,
        architectural_constraints=issue.architectural_constraints,
        agent_working=issue.agent_working if hasattr(issue, "agent_working") else None,
        reasoning_logs=[
            {
                "id": str(log.id),
                "timestamp": log.timestamp,
                "context": log.context.value,
                "reasoning": log.reasoning,
                "related_nodes": [str(n) for n in log.related_nodes],
            }
            for log in issue.reasoning_logs
        ],
        manifest_todo=issue.manifest_todo if hasattr(issue, "manifest_todo") else [],
        manifest_files=issue.manifest_files if hasattr(issue, "manifest_files") else [],
        manifest_notes=issue.manifest_notes if hasattr(issue, "manifest_notes") else [],
        agent_started_at=issue.agent_started_at if hasattr(issue, "agent_started_at") else None,
        agent_finished_at=issue.agent_finished_at if hasattr(issue, "agent_finished_at") else None,
        agent_id=issue.agent_id if hasattr(issue, "agent_id") else None,
    )


def _component_to_response(comp: Component) -> ComponentResponse:
    """Convert a domain Component to an API response model."""
    return ComponentResponse(
        id=str(comp.id),
        name=comp.name,
        description=comp.description,
        project=comp.project,
        created_at=comp.created_at,
        updated_at=comp.updated_at,
    )


def _paginated(items: list[Any], page: int, limit: int, total: int) -> PaginatedResponse[Any]:
    """Build a paginated response."""
    return PaginatedResponse(
        items=items,
        pagination=PaginationMeta(
            page=page,
            limit=limit,
            total=total,
            has_next=(page * limit) < total,
            has_prev=page > 1,
        ),
    )


# ---------------------------------------------------------------------------
# Issues router
# ---------------------------------------------------------------------------

issues_router = APIRouter()


@issues_router.post(
    "/issues",
    response_model=APIResponse[IssueResponse],
    status_code=201,
    summary="Create a new issue",
    description=(
        "Create a new issue in the task management system. "
        "The issue will be linked to an existing component and can have "
        "labels and architectural constraints assigned."
    ),
    responses={
        201: {"description": "Issue created successfully"},
        404: {"description": "Component not found"},
        400: {"description": "Validation error"},
    },
)
def create_issue(
    body: IssueCreateRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[IssueResponse]:
    from fastapi import HTTPException
    from socialseed_tasker.core.validation import (
        IssueDescriptionValidationError,
        IssueTitleValidationError,
        sanitize_issue_description,
        sanitize_issue_title,
        validate_issue_title,
    )

    try:
        validated_title = validate_issue_title(body.title)
    except IssueTitleValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        sanitized_description = sanitize_issue_description(body.description or "")
    except IssueDescriptionValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sanitized_title = sanitize_issue_title(validated_title)

    issue, warnings = create_issue_action(
        repo,
        title=sanitized_title,
        component_id=body.component_id,
        description=sanitized_description,
        priority=body.priority,
        labels=body.labels,
        architectural_constraints=body.architectural_constraints,
    )
    return APIResponse(
        data=_issue_to_response(issue), meta=Meta(request_id=None, warnings=warnings if warnings else None)
    )


@issues_router.get(
    "/issues",
    response_model=APIResponse[PaginatedResponse[IssueResponse]],
    summary="List issues",
    description=(
        "List issues with optional filters for status, component, and labels. "
        "Supports pagination via page and limit query parameters."
    ),
)
def list_issues(
    status: str | None = Query(None, description="Filter by status"),
    component: str | None = Query(None, description="Filter by component ID"),
    project: str | None = Query(None, description="Filter by project name"),
    page: int = Query(1, ge=1, description="Page number (starts at 1, default: 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (default: 20, max: 100)"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    status_filter = IssueStatus(status) if status else None
    all_issues = repo.list_issues(component_id=component, status=status_filter, project=project)
    total = len(all_issues)
    start = (page - 1) * limit
    end = start + limit
    page_items = all_issues[start:end]

    return APIResponse(
        data=_paginated([_issue_to_response(i) for i in page_items], page, limit, total),
        meta=Meta(request_id=None),
    )


@issues_router.get(
    "/issues/{issue_id}",
    response_model=APIResponse[IssueResponse],
    summary="Get issue details",
    description="Retrieve full details of a single issue by its ID.",
    responses={404: {"description": "Issue not found"}},
)
def get_issue(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)
    return APIResponse(data=_issue_to_response(issue), meta=Meta(request_id=None))


@issues_router.patch(
    "/issues/{issue_id}",
    response_model=APIResponse[IssueResponse],
    summary="Update an issue",
    description="Partially update an issue's fields. Supports: status, priority, labels, description, agent_working.",
    responses={
        404: {"description": "Issue not found"},
        400: {"description": "Invalid status transition or validation error"},
    },
)
def update_issue(
    issue_id: str,
    body: IssueUpdateRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    from fastapi import HTTPException

    existing = repo.get_issue(issue_id)
    if existing is None:
        raise IssueNotFoundError(issue_id)

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return APIResponse(data=_issue_to_response(existing), meta=Meta(request_id=None))

    if "status" in updates:
        new_status = IssueStatus(updates["status"])
        if existing.status == IssueStatus.CLOSED and new_status != IssueStatus.CLOSED:
            raise HTTPException(
                status_code=400,
                detail="Cannot reopen a closed issue. Use a separate reopen endpoint or create a new issue.",
            )
        if "agent_working" in updates and new_status not in (
            IssueStatus.OPEN,
            IssueStatus.IN_PROGRESS,
            IssueStatus.BLOCKED,
        ):
            raise HTTPException(
                status_code=400,
                detail="agent_working can only be set on OPEN, IN_PROGRESS, or BLOCKED issues.",
            )

    if "agent_working" in updates and "status" not in updates:
        if existing.status not in (IssueStatus.OPEN, IssueStatus.IN_PROGRESS, IssueStatus.BLOCKED):
            raise HTTPException(
                status_code=400,
                detail="agent_working can only be set on OPEN, IN_PROGRESS, or BLOCKED issues.",
            )

    updated = repo.update_issue(issue_id, updates)
    return APIResponse(data=_issue_to_response(updated), meta=Meta(request_id=None))


@issues_router.delete(
    "/issues/{issue_id}",
    status_code=204,
    summary="Delete an issue",
    description="Permanently delete an issue and all its relationships.",
    responses={404: {"description": "Issue not found"}},
)
def delete_issue(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)
    repo.delete_issue(issue_id)


@issues_router.post(
    "/issues/{issue_id}/close",
    response_model=APIResponse[IssueResponse],
    summary="Close an issue",
    description=("Close an issue. Fails if the issue has open dependencies or is already closed."),
    responses={
        404: {"description": "Issue not found"},
        409: {"description": "Already closed or has open dependencies"},
    },
)
def close_issue(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    issue = close_issue_action(repo, issue_id)
    return APIResponse(data=_issue_to_response(issue), meta=Meta(request_id=None))


@issues_router.post(
    "/issues/{issue_id}/link-github",
    response_model=APIResponse[IssueResponse],
    summary="Link GitHub issue",
    description="Link a Tasker issue to a GitHub issue for causal mirroring.",
)
def link_github_issue(
    issue_id: str,
    github_issue_url: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[IssueResponse]:
    import re

    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    match = re.search(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)", github_issue_url)
    if not match:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Invalid GitHub issue URL")

    github_issue_number = int(match.group(3))

    updates = {
        "github_issue_url": github_issue_url,
        "github_issue_number": github_issue_number,
    }
    updated_issue = repo.update_issue(issue_id, updates)
    return APIResponse(data=_issue_to_response(updated_issue), meta=Meta(request_id=None))


@issues_router.post(
    "/issues/{issue_id}/unlink-github",
    response_model=APIResponse[IssueResponse],
    summary="Unlink GitHub issue",
    description="Unlink a Tasker issue from its GitHub issue.",
)
def unlink_github_issue(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[IssueResponse]:
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    updates = {
        "github_issue_url": None,
        "github_issue_number": None,
    }
    updated_issue = repo.update_issue(issue_id, updates)
    return APIResponse(data=_issue_to_response(updated_issue), meta=Meta(request_id=None))


@issues_router.post(
    "/issues/{issue_id}/mirror-root-cause",
    response_model=APIResponse[dict],
    summary="Mirror root cause analysis to GitHub",
    description="Post root cause analysis as a comment on the linked GitHub issue.",
)
def mirror_root_cause(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[dict]:
    from socialseed_tasker.core.services.github_mirror import GitHubMirroringService

    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    if not hasattr(issue, "github_issue_number") or not issue.github_issue_number:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Issue not linked to GitHub")

    from socialseed_tasker.core.project_analysis.analyzer import ArchitecturalAnalyzer

    analyzer = ArchitecturalAnalyzer(repo)

    causal_links = analyzer.analyze_root_cause_issues([issue])

    if not causal_links:
        return APIResponse(
            data={"mirrored": False, "message": "No causal links found"},
            meta=Meta(request_id=None),
        )

    analysis_data = {
        "confidence": max([c.confidence for c in causal_links]) if causal_links else 0.0,
        "primary_factor": "Multiple causal factors identified",
        "causal_links": [{"issue_id": str(c.issue.id), "issue_title": c.issue.title} for c in causal_links[:5]],
    }

    mirror = GitHubMirroringService()
    result = mirror.mirror_root_cause(issue.github_issue_number, analysis_data)
    mirror.close()

    return APIResponse(
        data={"mirrored": True, "comment_url": result.get("html_url")},
        meta=Meta(request_id=None),
    )


@issues_router.post(
    "/issues/{issue_id}/mirror-impact",
    response_model=APIResponse[dict],
    summary="Mirror impact analysis to GitHub",
    description="Post impact analysis as a comment on the linked GitHub issue.",
)
def mirror_impact(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[dict]:
    from socialseed_tasker.core.services.github_mirror import GitHubMirroringService

    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    if not hasattr(issue, "github_issue_number") or not issue.github_issue_number:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Issue not linked to GitHub")

    from socialseed_tasker.core.project_analysis.analyzer import ArchitecturalAnalyzer

    analyzer = ArchitecturalAnalyzer(repo)
    analysis = analyzer.analyze_impact(issue.id)

    analysis_data = {
        "directly_affected": [{"id": str(i.id), "title": i.title} for i in analysis.directly_affected],
        "transitively_affected": [{"id": str(i.id), "title": i.title} for i in analysis.transitively_affected],
        "blocked_issues": [{"id": str(i.id), "title": i.title} for i in analysis.blocked_issues],
        "affected_components": analysis.affected_components,
        "risk_level": analysis.risk_level.value,
    }

    mirror = GitHubMirroringService()
    result = mirror.mirror_impact(issue.github_issue_number, analysis_data)
    mirror.close()

    return APIResponse(
        data={"mirrored": True, "comment_url": result.get("html_url")},
        meta=Meta(request_id=None),
    )


@issues_router.post(
    "/issues/{issue_id}/reasoning",
    response_model=APIResponse[IssueResponse],
    summary="Add reasoning log entry",
    description=(
        "Add a reasoning log entry to an issue. "
        "Captures the AI's decision-making process for transparency and auditability."
    ),
    responses={
        404: {"description": "Issue not found"},
    },
)
def add_reasoning_log(
    issue_id: str,
    body: ReasoningLogEntryRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[IssueResponse]:
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    from uuid import UUID

    related_nodes = [UUID(n) for n in body.related_nodes] if body.related_nodes else []
    updated_issue = repo.add_reasoning_log(
        issue_id=issue_id,
        context=body.context,
        reasoning=body.reasoning,
        related_nodes=body.related_nodes,
    )
    return APIResponse(data=_issue_to_response(updated_issue), meta=Meta(request_id=None))


@issues_router.get(
    "/issues/{issue_id}/reasoning",
    response_model=APIResponse[list[ReasoningLogEntryResponse]],
    summary="Get reasoning logs",
    description="Get all reasoning log entries for an issue.",
    responses={
        404: {"description": "Issue not found"},
    },
)
def get_reasoning_logs(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[list[ReasoningLogEntryResponse]]:
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    logs = repo.get_reasoning_logs(issue_id)
    log_responses = [
        ReasoningLogEntryResponse(
            id=log.get("id", ""),
            timestamp=log.get("timestamp", ""),
            context=log.get("context", ""),
            reasoning=log.get("reasoning", ""),
            related_nodes=log.get("related_nodes", []),
        )
        for log in logs
    ]
    return APIResponse(data=log_responses, meta=Meta(request_id=None))


@issues_router.patch(
    "/issues/{issue_id}/manifest/todo",
    response_model=APIResponse[IssueResponse],
    summary="Update manifest TODO list",
    description=(
        "Update the agent progress manifest TODO list. "
        "Maintains real-time documentation of sub-tasks with completion status."
    ),
    responses={
        404: {"description": "Issue not found"},
    },
)
def update_manifest_todo(
    issue_id: str,
    body: ManifestTodoRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[IssueResponse]:
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    todo_list = [{"task": item.task, "completed": str(item.completed)} for item in body.todo]
    updated_issue = repo.update_manifest_todo(issue_id, todo_list)
    return APIResponse(data=_issue_to_response(updated_issue), meta=Meta(request_id=None))


@issues_router.patch(
    "/issues/{issue_id}/manifest/files",
    response_model=APIResponse[IssueResponse],
    summary="Update manifest affected files",
    description=(
        "Update the agent progress manifest with affected files. Tracks created or modified file paths in real-time."
    ),
    responses={
        404: {"description": "Issue not found"},
    },
)
def update_manifest_files(
    issue_id: str,
    body: ManifestFilesRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[IssueResponse]:
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    updated_issue = repo.update_manifest_files(issue_id, body.files)
    return APIResponse(data=_issue_to_response(updated_issue), meta=Meta(request_id=None))


@issues_router.patch(
    "/issues/{issue_id}/manifest/notes",
    response_model=APIResponse[IssueResponse],
    summary="Update manifest technical debt notes",
    description=(
        "Update the agent progress manifest with technical debt notes. Records observations made during implementation."
    ),
    responses={
        404: {"description": "Issue not found"},
    },
)
def update_manifest_notes(
    issue_id: str,
    body: ManifestNotesRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[IssueResponse]:
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    updated_issue = repo.update_manifest_notes(issue_id, body.notes)
    return APIResponse(data=_issue_to_response(updated_issue), meta=Meta(request_id=None))


@issues_router.get(
    "/issues/{issue_id}/manifest",
    response_model=APIResponse[ManifestResponse],
    summary="Get manifest",
    description="Get the full agent progress manifest for an issue.",
    responses={
        404: {"description": "Issue not found"},
    },
)
def get_manifest(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[ManifestResponse]:
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    manifest = repo.get_manifest(issue_id)
    return APIResponse(
        data=ManifestResponse(
            todo=manifest.get("todo", []),
            files=manifest.get("files", []),
            notes=manifest.get("notes", []),
        ),
        meta=Meta(request_id=None),
    )


@issues_router.post(
    "/issues/{issue_id}/agent/start",
    response_model=APIResponse[IssueResponse],
    summary="Start agent work",
    description="Start agent work on an issue. Requires agent_working=false.",
    responses={
        404: {"description": "Issue not found"},
        409: {"description": "Agent is already working on this issue"},
    },
)
def start_agent_work(
    issue_id: str,
    body: AgentStartRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[IssueResponse]:
    try:
        issue = repo.get_issue(issue_id)
        if issue is None:
            raise IssueNotFoundError(issue_id)

        if hasattr(issue, "agent_working") and issue.agent_working:
            from fastapi import HTTPException

            raise HTTPException(
                status_code=409,
                detail=f"Agent is already working on issue {issue_id}",
            )

        updated_issue = repo.start_agent_work(issue_id, body.agent_id)
        return APIResponse(data=_issue_to_response(updated_issue), meta=Meta(request_id=None))
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=409, detail=str(e))


@issues_router.post(
    "/issues/{issue_id}/agent/finish",
    response_model=APIResponse[IssueResponse],
    summary="Finish agent work",
    description="Finish agent work on an issue. Requires agent_working=true.",
    responses={
        404: {"description": "Issue not found"},
        409: {"description": "Agent is not working on this issue"},
    },
)
def finish_agent_work(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[IssueResponse]:
    try:
        issue = repo.get_issue(issue_id)
        if issue is None:
            raise IssueNotFoundError(issue_id)

        updated_issue = repo.finish_agent_work(issue_id)
        return APIResponse(data=_issue_to_response(updated_issue), meta=Meta(request_id=None))
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=409, detail=str(e))


@issues_router.get(
    "/issues/{issue_id}/agent/status",
    response_model=APIResponse[AgentStatusResponse],
    summary="Get agent status",
    description="Get agent work status for an issue.",
    responses={
        404: {"description": "Issue not found"},
    },
)
def get_agent_status(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[AgentStatusResponse]:
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    status = repo.get_agent_status(issue_id)
    return APIResponse(
        data=AgentStatusResponse(
            agent_working=status.get("agent_working", False),
            agent_started_at=status.get("agent_started_at"),
            agent_finished_at=status.get("agent_finished_at"),
            agent_id=status.get("agent_id"),
        ),
        meta=Meta(request_id=None),
    )


# ---------------------------------------------------------------------------
# Dependencies router
# ---------------------------------------------------------------------------

dependencies_router = APIRouter()


@dependencies_router.post(
    "/issues/{issue_id}/dependencies",
    response_model=APIResponse[DependencyResponse],
    status_code=201,
    summary="Add a dependency",
    description=("Create a [:DEPENDS_ON] relationship. Fails if adding it would create a circular dependency."),
    responses={
        404: {"description": "Issue not found"},
        409: {"description": "Circular dependency detected"},
    },
)
def add_dependency(
    issue_id: str,
    body: DependencyRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
    request: Request = None,
):
    from socialseed_tasker.core.project_analysis.policy import PolicyEngine
    from socialseed_tasker.core.task_management.actions import PolicyViolationError

    policies = _policy_engine.get("policies", [])
    if policies and request and hasattr(request.app.state, "config"):
        enforcement_mode = getattr(request.app.state.config, "policy_enforcement_mode", "warn")

        if enforcement_mode != "disabled":
            engine = PolicyEngine(policies)

            issue = repo.get_issue(issue_id)
            target = repo.get_issue(body.depends_on_id)

            if issue and target:
                from_component = repo.get_component(str(issue.component_id))
                to_component = repo.get_component(str(target.component_id))

                result = engine.validate_dependency(
                    from_component_name=from_component.name if from_component else "",
                    from_component_type=from_component.project if from_component else "",
                    from_labels=issue.labels,
                    to_component_name=to_component.name if to_component else "",
                    to_component_type=to_component.project if to_component else "",
                    to_labels=target.labels,
                )

                if result.has_violations and enforcement_mode == "block":
                    violation = result.violations[0]
                    raise PolicyViolationError(
                        policy_name=violation.policy_name,
                        rule_type=violation.rule_type.value,
                        message=violation.message,
                        suggestion=violation.suggestion,
                    )

    add_dependency_action(repo, issue_id, body.depends_on_id)
    return APIResponse(
        data=DependencyResponse(issue_id=issue_id, depends_on_id=body.depends_on_id),
        meta=Meta(request_id=None),
    )


@dependencies_router.post(
    "/issues/{issue_id}/dependencies/bulk",
    response_model=APIResponse[BulkDependencyResponse],
    summary="Add multiple dependencies",
    description="Add multiple [:DEPENDS_ON] relationships in a single request. Validates all dependencies and returns detailed results.",
    responses={
        404: {"description": "Issue not found"},
        409: {"description": "Circular dependency detected"},
    },
)
def add_dependencies_bulk(
    issue_id: str,
    body: BulkDependencyRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    from socialseed_tasker.core.task_management.actions import (
        CircularDependencyError,
        IssueNotFoundError,
    )

    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)

    successful = 0
    failed = 0
    results = []

    for dep_id in body.depends_on_ids:
        try:
            add_dependency_action(repo, issue_id, dep_id)
            successful += 1
            results.append({"depends_on_id": dep_id, "status": "created"})
        except IssueNotFoundError:
            failed += 1
            results.append({"depends_on_id": dep_id, "status": "error", "message": "Target issue not found"})
        except CircularDependencyError as e:
            failed += 1
            results.append({"depends_on_id": dep_id, "status": "error", "message": str(e)})
        except Exception as e:
            failed += 1
            results.append({"depends_on_id": dep_id, "status": "error", "message": str(e)})

    return APIResponse(
        data=BulkDependencyResponse(
            issue_id=issue_id,
            total_requested=len(body.depends_on_ids),
            successful=successful,
            failed=failed,
            results=results,
        ),
        meta=Meta(request_id=None),
    )


@dependencies_router.delete(
    "/issues/{issue_id}/dependencies/{depends_on_id}",
    status_code=204,
    summary="Remove a dependency",
    description="Remove a [:DEPENDS_ON] relationship between two issues.",
    responses={404: {"description": "Issue not found"}},
)
def remove_dependency(
    issue_id: str,
    depends_on_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    remove_dependency_action(repo, issue_id, depends_on_id)


@dependencies_router.get(
    "/issues/{issue_id}/dependencies",
    response_model=APIResponse[PaginatedResponse[IssueResponse]],
    summary="List dependencies",
    description="List all issues that this issue depends on.",
)
def list_dependencies(
    issue_id: str,
    page: int = Query(1, ge=1, description="Page number (starts at 1, default: 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (default: 20, max: 100)"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)
    deps = repo.get_dependencies(issue_id)
    total = len(deps)
    start = (page - 1) * limit
    end = start + limit
    page_items = deps[start:end]
    return APIResponse(
        data=_paginated([_issue_to_response(d) for d in page_items], page, limit, total),
        meta=Meta(request_id=None),
    )


@dependencies_router.get(
    "/issues/{issue_id}/dependents",
    response_model=APIResponse[list[IssueResponse]],
    summary="List dependents",
    description="List all issues that depend on this issue.",
)
def list_dependents(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)
    dependents = repo.get_dependents(issue_id)
    return APIResponse(data=[_issue_to_response(d) for d in dependents], meta=Meta(request_id=None))


@dependencies_router.get(
    "/issues/{issue_id}/dependency-chain",
    response_model=APIResponse[list[IssueResponse]],
    summary="Get dependency chain",
    description="Get the full transitive dependency chain for an issue.",
)
def get_dependency_chain(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    chain = get_dependency_chain_action(repo, issue_id)
    return APIResponse(data=[_issue_to_response(i) for i in chain], meta=Meta(request_id=None))


@dependencies_router.get(
    "/blocked-issues",
    response_model=APIResponse[list[IssueResponse]],
    summary="List blocked issues",
    description="List all issues blocked by at least one open dependency.",
)
def list_blocked_issues(
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    blocked = get_blocked_issues_action(repo)
    return APIResponse(data=[_issue_to_response(i) for i in blocked], meta=Meta(request_id=None))


@dependencies_router.get(
    "/workable-issues",
    response_model=APIResponse[list[IssueResponse]],
    summary="List workable issues",
    description=(
        "List all issues that are ready to work on. "
        "An issue is workable if its status is not CLOSED and all its dependencies are CLOSED. "
        "Supports filtering by priority and component."
    ),
)
def list_workable_issues(
    priority: str | None = Query(None, description="Filter by priority (HIGH, MEDIUM, LOW)"),
    component: str | None = Query(None, description="Filter by component ID"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    workable = get_workable_issues_action(repo, priority=priority, component_id=component)
    return APIResponse(data=[_issue_to_response(i) for i in workable], meta=Meta(request_id=None))


# ---------------------------------------------------------------------------
# Components router
# ---------------------------------------------------------------------------

components_router = APIRouter()


@components_router.post(
    "/components",
    response_model=APIResponse[ComponentResponse],
    status_code=201,
    summary="Create a component",
    description="Create a new component to group issues.",
)
def create_component(
    body: ComponentCreateRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    from fastapi import HTTPException
    from socialseed_tasker.core.task_management.entities import Component
    from socialseed_tasker.core.validation import (
        ComponentNameValidationError,
        sanitize_component_name,
        validate_component_name,
    )

    try:
        validated_name = validate_component_name(body.name)
    except ComponentNameValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sanitized_name = sanitize_component_name(validated_name)
    sanitized_description = sanitize_component_name(body.description or "")

    comp = Component(name=sanitized_name, description=sanitized_description, project=body.project)
    repo.create_component(comp)
    return APIResponse(data=_component_to_response(comp), meta=Meta(request_id=None))


@components_router.get(
    "/components",
    response_model=APIResponse[PaginatedResponse[ComponentResponse]],
    summary="List components",
    description="List all components, optionally filtered by project or name. Supports pagination.",
)
def list_components(
    project: str | None = Query(None, description="Filter by project"),
    name: str | None = Query(None, description="Filter by exact name"),
    page: int = Query(1, ge=1, description="Page number (starts at 1, default: 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (default: 20, max: 100)"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    if name:
        comp = repo.get_component_by_name(name, project)
        components = [comp] if comp else []
    else:
        components = repo.list_components(project=project)

    total = len(components)
    start = (page - 1) * limit
    end = start + limit
    page_items = components[start:end]

    return APIResponse(
        data=_paginated([_component_to_response(c) for c in page_items], page, limit, total),
        meta=Meta(request_id=None),
    )


@components_router.get(
    "/components/{component_id}",
    response_model=APIResponse[ComponentResponse],
    summary="Get component details",
    description="Retrieve full details of a single component.",
    responses={404: {"description": "Component not found"}},
)
def get_component(
    component_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    comp = repo.get_component(component_id)
    if comp is None:
        raise ComponentNotFoundError(component_id)
    return APIResponse(data=_component_to_response(comp), meta=Meta(request_id=None))


@components_router.patch(
    "/components/{component_id}",
    response_model=APIResponse[ComponentResponse],
    summary="Update a component",
    description="Update one or more fields of a component.",
)
def update_component(
    component_id: str,
    body: dict[str, Any],
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[ComponentResponse]:

    try:
        updates = {}
        if "name" in body:
            updates["name"] = body["name"]
        if "description" in body:
            updates["description"] = body["description"]
        if "project" in body:
            updates["project"] = body["project"]

        if not updates:
            raise ValueError("At least one field to update must be provided")

        updated = repo.update_component(component_id, updates)
        return APIResponse(data=_component_to_response(updated), meta=Meta(request_id=None))
    except FileNotFoundError:
        raise ComponentNotFoundError(component_id)
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(e))


@components_router.delete(
    "/components/{component_id}",
    response_model=APIResponse[dict[str, Any]],
    summary="Delete a component",
    description="Delete a component. Fails if component has issues unless force=true.",
)
def delete_component(
    component_id: str,
    force: bool = Query(False, description="Force deletion even if component has issues"),
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[dict[str, str]]:
    from socialseed_tasker.core.task_management.actions import ComponentHasIssuesError, delete_component_action

    try:
        delete_component_action(repo, component_id, force=force)
        return APIResponse(data={"deleted": component_id}, meta=Meta(request_id=None))
    except FileNotFoundError:
        raise ComponentNotFoundError(component_id)
    except ComponentHasIssuesError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=409, detail=str(e))


# ---------------------------------------------------------------------------
# Label router
# ---------------------------------------------------------------------------

label_router = APIRouter()


@label_router.get(
    "/labels",
    response_model=APIResponse[list[dict]],
    summary="List all labels",
    description="List all labels synced from GitHub or created in Tasker.",
)
def list_labels(
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[list[dict]]:
    labels = repo.get_all_labels() if hasattr(repo, "get_all_labels") else []
    return APIResponse(data=labels, meta=Meta(request_id=None))


@label_router.post(
    "/labels/sync",
    response_model=APIResponse[dict],
    summary="Sync labels from GitHub",
    description="Force sync labels from GitHub repository to Neo4j.",
)
def sync_labels(
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[dict]:
    from socialseed_tasker.storage.adapters.github import GitHubAdapter

    try:
        adapter = GitHubAdapter()
        synced = repo.sync_labels_from_github(adapter)
        adapter.close()
        return APIResponse(data={"synced": synced}, meta=Meta(request_id=None))
    except Exception as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail=str(e))


@label_router.get(
    "/issues",
    response_model=APIResponse[list[IssueResponse]],
    summary="List issues",
    description="List issues with optional filtering by labels, status, component, or project.",
)
def list_issues(
    labels: str | None = Query(None, description="Filter by comma-separated labels"),
    status: str | None = Query(None, description="Filter by status"),
    component_id: str | None = Query(None, description="Filter by component"),
    project: str | None = Query(None, description="Filter by project"),
    page: int = Query(1, ge=1, description="Page number (starts at 1, default: 1)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (default: 20, max: 100)"),
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[list[IssueResponse]]:
    label_list = [l.strip() for l in labels.split(",")] if labels else []

    if label_list and hasattr(repo, "get_issues_by_labels"):
        issues = repo.get_issues_by_labels(label_list)
    else:
        issues = repo.list_issues(
            component_id=component_id,
            status=status,
            project=project,
        )

    start = (page - 1) * limit
    end = start + limit
    paginated = issues[start:end]

    return APIResponse(
        data=[_issue_to_response(i) for i in paginated],
        meta=Meta(request_id=None),
    )


# ---------------------------------------------------------------------------
# Analysis router (root-cause analysis and impact assessment)
# ---------------------------------------------------------------------------

analysis_router = APIRouter()


@analysis_router.post(
    "/analyze/root-cause",
    response_model=APIResponse[list[CausalLinkResponse]],
    summary="Find root cause of test failure (DEPRECATED)",
    description=(
        "DEPRECATED: Use /analyze/link-test instead. "
        "Submit a test failure and get potential root causes ranked by "
        "confidence. Uses graph proximity analysis to link failed tests "
        "to recently closed issues."
    ),
    deprecated=True,
)
def analyze_root_cause(
    body: TestFailureRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[list[CausalLinkResponse]]:
    analyzer = RootCauseAnalyzer(repo)
    test_failure = TestFailure(
        test_id=body.test_id,
        test_name=body.test_name,
        error_message=body.error_message,
        stack_trace=body.stack_trace,
        component=body.component,
        labels=body.labels,
    )

    all_issues = repo.list_issues()
    closed_issues = [i for i in all_issues if i.status.value == "CLOSED"]
    causal_links = analyzer.find_root_cause(test_failure, closed_issues)

    link_data = [
        CausalLinkResponse(
            issue_id=str(link.issue.id),
            issue_title=link.issue.title,
            confidence=link.confidence,
            reasons=link.reasons,
            graph_distance=link.graph_distance,
        )
        for link in causal_links
    ]
    return APIResponse(data=link_data, meta=Meta(request_id=None))


@analysis_router.post(
    "/analyze/link-test",
    response_model=APIResponse[list[CausalLinkResponse]],
    summary="Link test failure to root cause",
    description=(
        "Submit a test failure and get potential root causes ranked by "
        "confidence. Uses graph proximity analysis to link failed tests "
        "to recently closed issues. Use this endpoint when you have a "
        "failing test and want to find which closed issue might have caused it."
    ),
)
def link_test_failure(
    body: TestFailureRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[list[CausalLinkResponse]]:
    analyzer = RootCauseAnalyzer(repo)
    test_failure = TestFailure(
        test_id=body.test_id,
        test_name=body.test_name,
        error_message=body.error_message,
        stack_trace=body.stack_trace,
        component=body.component,
        labels=body.labels,
    )

    all_issues = repo.list_issues()
    closed_issues = [i for i in all_issues if i.status.value == "CLOSED"]
    causal_links = analyzer.find_root_cause(test_failure, closed_issues)

    link_data = [
        CausalLinkResponse(
            issue_id=str(link.issue.id),
            issue_title=link.issue.title,
            confidence=link.confidence,
            reasons=link.reasons,
            graph_distance=link.graph_distance,
        )
        for link in causal_links
    ]
    return APIResponse(data=link_data, meta=Meta(request_id=None))


@analysis_router.get(
    "/analyze/impact/{issue_id}",
    response_model=APIResponse[ImpactAnalysisResponse],
    summary="Get impact analysis",
    description="Analyse what other issues and components would be affected.",
)
def analyze_impact(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[ImpactAnalysisResponse]:
    analyzer = RootCauseAnalyzer(repo)
    impact: ImpactAnalysis = analyzer.analyze_impact(issue_id)

    impact_data = ImpactAnalysisResponse(
        issue_id=str(impact.issue_id),
        directly_affected=[
            ImpactIssueSummary(id=str(i.id), title=i.title, status=i.status.value) for i in impact.directly_affected
        ],
        transitively_affected=[
            ImpactIssueSummary(id=str(i.id), title=i.title, status=i.status.value) for i in impact.transitively_affected
        ],
        blocked_issues=[
            ImpactIssueSummary(id=str(i.id), title=i.title, status=i.status.value) for i in impact.blocked_issues
        ],
        affected_components=impact.affected_components,
        risk_level=impact.risk_level.value,
    )
    return APIResponse(data=impact_data, meta=Meta(request_id=None))


@analysis_router.get(
    "/analyze/component-impact/{component_id}",
    response_model=APIResponse[ComponentImpactAnalysisResponse],
    summary="Get component impact analysis",
    description="Analyse the impact of an entire component across the project.",
)
def analyze_component_impact(
    component_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[ComponentImpactAnalysisResponse]:
    analyzer = RootCauseAnalyzer(repo)
    impact: ComponentImpactAnalysis = analyzer.analyze_component_impact(component_id)

    impact_data = ComponentImpactAnalysisResponse(
        component_id=str(impact.component_id),
        component_name=impact.component_name,
        total_issues=impact.total_issues,
        directly_affected_components=impact.directly_affected_components,
        transitively_affected_components=impact.transitively_affected_components,
        total_blocked_issues=impact.total_blocked_issues,
        criticality_score=impact.criticality_score,
        risk_level=impact.risk_level.value,
        affected_issues_summary=[
            ComponentImpactIssueSummary(id=i.id, title=i.title, status=i.status) for i in impact.affected_issues_summary
        ],
    )
    return APIResponse(data=impact_data, meta=Meta(request_id=None))


@analysis_router.get(
    "/graph/dependencies",
    response_model=APIResponse[DependencyGraphResponse],
    summary="Get full dependency graph",
    description="Return the complete dependency graph for visualization. Supports filtering by project.",
)
def get_full_dependency_graph(
    project: str | None = Query(None, description="Filter by project name"),
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[DependencyGraphResponse]:
    all_issues = repo.list_issues(project=project)
    components = {str(c.id): c.name for c in repo.list_components(project=project)}

    nodes = []
    edges = []

    for issue in all_issues:
        nodes.append(
            {
                "id": str(issue.id),
                "title": issue.title,
                "component": components.get(str(issue.component_id)),
                "status": issue.status.value,
                "priority": issue.priority.value,
            }
        )

    for issue in all_issues:
        for dep_id in issue.dependencies:
            edges.append(
                {
                    "from_node": str(issue.id),
                    "to_node": str(dep_id),
                }
            )

    return APIResponse(
        data=DependencyGraphResponse(nodes=nodes, edges=edges),
        meta=Meta(request_id=None),
    )


@analysis_router.get(
    "/graph/{issue_id}/subgraph",
    response_model=APIResponse[DependencyGraphResponse],
    summary="Get subgraph centered on issue",
    description="Return a subgraph centered on a specific issue with its dependencies and dependents.",
)
def get_subgraph(
    issue_id: str,
    depth: int = Query(2, ge=1, le=5, description="Maximum depth to traverse"),
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[DependencyGraphResponse]:
    from collections import deque

    center_issue = repo.get_issue(issue_id)
    if center_issue is None:
        raise IssueNotFoundError(issue_id)

    nodes: dict[str, dict] = {}
    edges: list[dict[str, str]] = []

    visited: set[str] = set()
    queue = deque([(issue_id, 0)])

    while queue:
        current_id, current_depth = queue.poplept()
        if current_id in visited or current_depth > depth:
            continue
        visited.add(current_id)

        issue = repo.get_issue(current_id)
        if issue is None:
            continue

        nodes[str(issue.id)] = {
            "id": str(issue.id),
            "title": issue.title,
            "status": issue.status.value,
            "priority": issue.priority.value,
        }

        if current_id != issue_id:
            edges.append({"from_node": current_id, "to_node": issue_id})

        if current_depth < depth:
            for dep_id in issue.dependencies:
                dep_id_str = str(dep_id)
                if dep_id_str not in visited:
                    edges.append({"from_node": str(issue.id), "to_node": dep_id_str})
                    queue.append((dep_id_str, current_depth + 1))

            for dep in repo.get_dependents(current_id):
                dep_id_str = str(dep.id)
                if dep_id_str not in visited:
                    edges.append({"from_node": dep_id_str, "to_node": str(issue.id)})
                    queue.append((dep_id_str, current_depth + 1))

    components = {str(c.id): c.name for c in repo.list_components()}
    for node_id, node_data in nodes.items():
        issue = repo.get_issue(node_id)
        if issue:
            node_data["component"] = components.get(str(issue.component_id))

    return APIResponse(
        data=DependencyGraphResponse(nodes=list(nodes.values()), edges=edges),
        meta=Meta(request_id=None),
    )


# ---------------------------------------------------------------------------
# Policy router
# ---------------------------------------------------------------------------

policy_router = APIRouter()


@policy_router.post(
    "/policies/validate",
    response_model=APIResponse[PolicyValidationResponse],
    summary="Validate action against policies",
    description="Check if an action would violate any architectural rules without actually performing the action.",
)
def validate_policy(
    body: PolicyValidationRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
    request: Request = None,
) -> APIResponse[PolicyValidationResponse]:
    from uuid import UUID
    from socialseed_tasker.core.project_analysis.analyzer import ArchitecturalAnalyzer
    from socialseed_tasker.core.project_analysis.rules import Severity
    from socialseed_tasker.core.task_management.entities import Issue, IssuePriority, IssueStatus

    enforcement_mode = "warn"
    if request and hasattr(request.app.state, "config"):
        enforcement_mode = getattr(request.app.state.config, "policy_enforcement_mode", "warn")

    analyzer = ArchitecturalAnalyzer(repo)
    violations = []

    if body.action_type == "create_issue" and body.issue_data:
        issue_data = body.issue_data
        issue = Issue(
            id=UUID(),
            title=issue_data.get("title", ""),
            description=issue_data.get("description", ""),
            status=IssueStatus.OPEN,
            priority=IssuePriority(issue_data.get("priority", "MEDIUM")),
            component_id=UUID(issue_data.get("component_id", "")),
            labels=issue_data.get("labels", []),
        )
        result = analyzer.validate_issue_creation(issue)
        for v in result.violations:
            violations.append(
                PolicyViolationResponse(
                    rule_id=str(v.rule_id),
                    rule_name=v.rule_name,
                    severity=v.severity.value,
                    message=v.message,
                    suggestion=v.suggestion,
                )
            )
    elif body.action_type == "add_dependency" and body.dependency_data:
        dep_data = body.dependency_data
        issue_id = dep_data.get("issue_id", "")
        depends_on_id = dep_data.get("depends_on_id", "")
        result = analyzer.validate_dependency(issue_id, depends_on_id)
        for v in result.violations:
            violations.append(
                PolicyViolationResponse(
                    rule_id=str(v.rule_id),
                    rule_name=v.rule_name,
                    severity=v.severity.value,
                    message=v.message,
                    suggestion=v.suggestion,
                )
            )

    has_errors = any(v.severity == "ERROR" for v in violations)

    return APIResponse(
        data=PolicyValidationResponse(
            is_valid=not has_errors or enforcement_mode == "disabled",
            violations=violations,
            enforcement_mode=enforcement_mode,
        ),
        meta=Meta(request_id=None),
    )


@policy_router.get(
    "/policies/rules",
    response_model=APIResponse[list[dict]],
    summary="Get active policy rules",
    description="List all active architectural rules.",
)
def get_policy_rules(
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[list[dict]]:
    from socialseed_tasker.core.project_analysis.analyzer import ArchitecturalAnalyzer
    from socialseed_tasker.core.task_management.entities import Issue, IssueStatus

    analyzer = ArchitecturalAnalyzer(repo)
    rules = analyzer.list_rules()

    rules_data = [
        {
            "id": str(r.id),
            "name": r.name,
            "description": r.description,
            "rule_type": r.rule_type.value,
            "severity": r.severity.value,
            "is_active": r.is_active,
        }
        for r in rules
    ]

    return APIResponse(data=rules_data, meta=Meta(request_id=None))


# In-memory policy storage for demonstration
_policy_engine: dict[str, Any] = {"policies": []}


@policy_router.post(
    "/policies",
    response_model=APIResponse[PolicyResponse],
    status_code=201,
    summary="Create a policy",
    description="Create a new policy with rules for architectural governance.",
)
def create_policy(
    body: PolicyCreateRequest,
) -> APIResponse[PolicyResponse]:
    from uuid import UUID
    from socialseed_tasker.core.project_analysis.policy import Policy, PolicyRule, PolicyRuleType

    rules = []
    for rule_req in body.rules:
        rules.append(
            PolicyRule(
                rule_type=PolicyRuleType(rule_req.rule_type),
                from_pattern=rule_req.from_pattern,
                to_pattern=rule_req.to_pattern,
                max_depth=rule_req.max_depth,
                description=rule_req.description,
            )
        )

    policy = Policy(
        name=body.name,
        description=body.description,
        rules=rules,
        is_active=body.is_active,
    )

    _policy_engine["policies"].append(policy)

    return APIResponse(
        data=PolicyResponse(
            id=str(policy.id),
            name=policy.name,
            description=policy.description,
            rules=[
                {"rule_type": r.rule_type.value, "from_pattern": r.from_pattern, "to_pattern": r.to_pattern}
                for r in policy.rules
            ],
            is_active=policy.is_active,
            created_at=policy.created_at,
            updated_at=policy.updated_at,
        ),
        meta=Meta(request_id=None),
    )


@policy_router.get(
    "/policies",
    response_model=APIResponse[list[PolicyResponse]],
    summary="List policies",
    description="List all policies.",
)
def list_policies() -> APIResponse[list[PolicyResponse]]:
    policies = _policy_engine.get("policies", [])
    return APIResponse(
        data=[
            PolicyResponse(
                id=str(p.id),
                name=p.name,
                description=p.description,
                rules=[
                    {"rule_type": r.rule_type.value, "from_pattern": r.from_pattern, "to_pattern": r.to_pattern}
                    for r in p.rules
                ],
                is_active=p.is_active,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in policies
        ],
        meta=Meta(request_id=None),
    )


@policy_router.get(
    "/policies/{policy_id}",
    response_model=APIResponse[PolicyResponse],
    summary="Get a policy",
    description="Get a policy by ID.",
)
def get_policy(policy_id: str) -> APIResponse[PolicyResponse]:
    from uuid import UUID

    policies = _policy_engine.get("policies", [])
    for p in policies:
        if str(p.id) == policy_id:
            return APIResponse(
                data=PolicyResponse(
                    id=str(p.id),
                    name=p.name,
                    description=p.description,
                    rules=[
                        {"rule_type": r.rule_type.value, "from_pattern": r.from_pattern, "to_pattern": r.to_pattern}
                        for r in p.rules
                    ],
                    is_active=p.is_active,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                ),
                meta=Meta(request_id=None),
            )

    from fastapi import HTTPException

    raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")


@policy_router.delete(
    "/policies/{policy_id}",
    response_model=APIResponse[dict],
    summary="Delete a policy",
    description="Delete a policy by ID.",
)
def delete_policy(policy_id: str) -> APIResponse[dict]:
    policies = _policy_engine.get("policies", [])
    _policy_engine["policies"] = [p for p in policies if str(p.id) != policy_id]
    return APIResponse(data={"deleted": policy_id}, meta=Meta(request_id=None))


@policy_router.post(
    "/policies/dry-run",
    response_model=APIResponse[PolicyValidationResponse],
    summary="Dry-run validation",
    description="Validate an action against policies without actually executing it.",
)
def dry_run_policy(
    body: PolicyValidationRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[PolicyValidationResponse]:
    from uuid import UUID
    from socialseed_tasker.core.project_analysis.policy import PolicyEngine

    violations = []

    if body.action_type == "add_dependency" and body.dependency_data:
        dep_data = body.dependency_data
        issue_id = dep_data.get("issue_id", "")
        depends_on_id = dep_data.get("depends_on_id", "")

        if issue_id and depends_on_id:
            issue = repo.get_issue(issue_id)
            target = repo.get_issue(depends_on_id)

            if issue and target:
                from_component = repo.get_component(str(issue.component_id))
                to_component = repo.get_component(str(target.component_id))

                policies = _policy_engine.get("policies", [])
                engine = PolicyEngine(policies)

                result = engine.validate_dependency(
                    from_component_name=from_component.name if from_component else "",
                    from_component_type=from_component.project if from_component else "",
                    from_labels=issue.labels,
                    to_component_name=to_component.name if to_component else "",
                    to_component_type=to_component.project if to_component else "",
                    to_labels=target.labels,
                )

                for v in result.violations:
                    violations.append(
                        PolicyViolationResponse(
                            rule_id=str(v.policy_id),
                            rule_name=v.policy_name,
                            severity="ERROR",
                            message=v.message,
                            suggestion=v.suggestion,
                        )
                    )

    return APIResponse(
        data=PolicyValidationResponse(
            is_valid=len(violations) == 0,
            violations=violations,
            enforcement_mode="dry-run",
        ),
        meta=Meta(request_id=None),
    )


# ---------------------------------------------------------------------------
# Project router
# ---------------------------------------------------------------------------

project_router = APIRouter()


@project_router.get(
    "/projects/{project_name}/summary",
    response_model=APIResponse[ProjectSummaryResponse],
    summary="Get project summary",
    description="Get an aggregated overview of a project including issue counts, dependency health, and critical path.",
)
def get_project_summary(
    project_name: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[ProjectSummaryResponse]:
    components = repo.list_components(project=project_name)
    all_issues = repo.list_issues(project=project_name)

    total_issues = len(all_issues)
    by_status: dict[str, int] = {}
    by_priority: dict[str, int] = {}

    for issue in all_issues:
        status = issue.status.value
        priority = issue.priority.value
        by_status[status] = by_status.get(status, 0) + 1
        by_priority[priority] = by_priority.get(priority, 0) + 1

    blocked_issues = get_blocked_issues_action(repo)
    blocked_filtered = [i for i in blocked_issues if any(str(i.component_id) == str(c.id) for c in components)]
    workable_issues = get_workable_issues_action(repo, component_id=None)
    workable_filtered = [i for i in workable_issues if any(str(i.component_id) == str(c.id) for c in components)]

    dependency_health = 0.0
    if total_issues > 0:
        issues_with_deps = sum(1 for i in all_issues if i.dependencies)
        if issues_with_deps > 0:
            closed_deps = sum(
                1
                for i in all_issues
                if i.dependencies
                and all(
                    next((d for d in all_issues if str(d.id) == str(dep_id) and d.status.value == "CLOSED"), None)
                    for dep_id in i.dependencies
                )
            )
            dependency_health = (closed_deps / issues_with_deps) * 100

    component_blocked_counts: dict[str, int] = {}
    for issue in blocked_filtered:
        comp_id = str(issue.component_id)
        component_blocked_counts[comp_id] = component_blocked_counts.get(comp_id, 0) + 1

    top_blocked = sorted(component_blocked_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    top_blocked_components = []
    for comp_id, count in top_blocked:
        comp = repo.get_component(comp_id)
        if comp:
            top_blocked_components.append({comp.name: count})

    critical_path_length = 0
    for issue in all_issues:
        chain = get_dependency_chain_action(repo, str(issue.id))
        if len(chain) > critical_path_length:
            critical_path_length = len(chain)

    return APIResponse(
        data=ProjectSummaryResponse(
            project=project_name,
            total_issues=total_issues,
            by_status=by_status,
            by_priority=by_priority,
            components_count=len(components),
            blocked_issues_count=len(blocked_filtered),
            workable_issues_count=len(workable_filtered),
            dependency_health=round(dependency_health, 1),
            top_blocked_components=top_blocked_components,
            critical_path_length=critical_path_length,
        ),
        meta=Meta(request_id=None),
    )


# ---------------------------------------------------------------------------
# Webhook router
# ---------------------------------------------------------------------------

webhook_router = APIRouter()


@webhook_router.post(
    "/webhooks/test-failure",
    response_model=APIResponse[TestFailureWebhookResponse],
    summary="Receive test failure events",
    description="Webhook endpoint to receive test failure events from socialseed-e2e. Automatically creates issues for failed tests.",
)
def receive_test_failure(
    body: TestFailureWebhookRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
    request: Request = None,
) -> APIResponse[TestFailureWebhookResponse]:
    import os

    webhook_api_key = os.environ.get("TASKER_WEBHOOK_API_KEY", "")
    if webhook_api_key:
        auth_header = request.headers.get("X-API-Key", "") if request else ""
        if auth_header != webhook_api_key:
            from fastapi import HTTPException

            raise HTTPException(status_code=401, detail="Invalid API key")

    component_id = None
    test_file = body.test_file
    if test_file:
        parts = test_file.replace("\\", "/").split("/")
        for part in parts:
            if part in ("src", "tests", "test"):
                continue
            if part.endswith(".py"):
                component_name = part.replace(".py", "").replace("test_", "")
                components = repo.list_components()
                for comp in components:
                    if comp.name.lower() == component_name.lower():
                        component_id = str(comp.id)
                        break
                if component_id:
                    break
        if not component_id:
            components = repo.list_components()
            if components:
                component_id = str(components[0].id)

    title = f"Test Failure: {body.test_name}"
    description = f"""## Test Failure Details

**Test Name:** {body.test_name}
**Test File:** {body.test_file}
**Test Type:** {body.test_type}
**Error Message:** {body.error_message}

**Stack Trace:**
```
{body.stack_trace}
```

**Commit:** {body.commit_sha}
**Branch:** {body.branch}
"""

    labels = ["test-failure", "auto-created", body.test_type]

    try:
        issue, warnings = create_issue_action(
            repo,
            title=title,
            component_id=component_id or "default",
            description=description,
            priority="HIGH",
            labels=labels,
        )
        return APIResponse(
            data=TestFailureWebhookResponse(
                issue_id=str(issue.id),
                message=f"Issue created for test failure: {body.test_name}",
                success=True,
            ),
            meta=Meta(request_id=None),
        )
    except ComponentNotFoundError:
        components = repo.list_components()
        if components:
            issue, warnings = create_issue_action(
                repo,
                title=title,
                component_id=str(components[0].id),
                description=description,
                priority="HIGH",
                labels=labels,
            )
            return APIResponse(
                data=TestFailureWebhookResponse(
                    issue_id=str(issue.id),
                    message=f"Issue created for test failure: {body.test_name}",
                    success=True,
                ),
                meta=Meta(request_id=None),
            )
        return APIResponse(
            data=TestFailureWebhookResponse(
                issue_id=None,
                message="No components found to assign issue",
                success=False,
            ),
            meta=Meta(request_id=None),
        )
    except Exception as e:
        return APIResponse(
            data=TestFailureWebhookResponse(
                issue_id=None,
                message=f"Failed to create issue: {str(e)}",
                success=False,
            ),
            meta=Meta(request_id=None),
        )


_github_webhook_logs: list[dict] = []


@webhook_router.post(
    "/webhooks/github",
    response_model=APIResponse[dict],
    summary="Receive GitHub webhook events",
    description="Receive real-time updates from GitHub (issues, comments, labels, milestones).",
)
def receive_github_webhook(
    repo: TaskRepositoryInterface = Depends(get_repo),
    request: Request = None,
) -> APIResponse[dict]:
    import json
    from datetime import datetime, timezone
    from socialseed_tasker.core.services.webhook_validator import get_webhook_validator

    if request is None:
        return APIResponse(
            data={"error": "No request context"},
            meta=Meta(request_id=None),
        )

    validator = get_webhook_validator()
    signature = request.headers.get("X-Hub-Signature-256", "")

    body = request.body()
    if not validator.validate(body, signature):
        from fastapi import HTTPException

        rejected_logs = validator.get_rejected_log()
        logger.warning(
            f"Webhook rejected: signature={signature[:20] if signature else 'none'}, rejected_count={len(rejected_logs)}"
        )
        raise HTTPException(status_code=401, detail="Invalid signature")

    event_type = request.headers.get("X-GitHub-Event", "unknown")
    payload = json.loads(body)

    log_entry = {
        "id": str(len(_github_webhook_logs)),
        "event_type": event_type,
        "delivery_status": "received",
        "received_at": datetime.now(timezone.utc).isoformat(),
        "processed_at": None,
        "error": None,
    }

    try:
        if event_type == "issues":
            action = payload.get("action", "")
            issue = payload.get("issue", {})

            if action in ("opened", "closed", "reopened"):
                pass

        elif event_type == "issue_comment":
            comment = payload.get("comment", {})

        elif event_type == "label":
            label = payload.get("label", {})

        elif event_type == "milestone":
            milestone = payload.get("milestone", {})

        log_entry["delivery_status"] = "processed"
        log_entry["processed_at"] = datetime.now(timezone.utc).isoformat()

    except Exception as e:
        log_entry["delivery_status"] = "error"
        log_entry["error"] = str(e)

    _github_webhook_logs.append(log_entry)
    if len(_github_webhook_logs) > 100:
        _github_webhook_logs.pop(0)

    return APIResponse(
        data={"received": True, "event": event_type},
        meta=Meta(request_id=None),
    )


@webhook_router.get(
    "/webhooks/github/logs",
    response_model=APIResponse[list[GitHubWebhookLogResponse]],
    summary="Get webhook delivery logs",
    description="View GitHub webhook delivery logs for debugging.",
)
def get_webhook_logs() -> APIResponse[list[GitHubWebhookLogResponse]]:
    logs = [
        GitHubWebhookLogResponse(
            id=log["id"],
            event_type=log["event_type"],
            delivery_status=log["delivery_status"],
            received_at=log["received_at"],
            processed_at=log.get("processed_at"),
            error=log.get("error"),
        )
        for log in _github_webhook_logs
    ]
    return APIResponse(data=logs, meta=Meta(request_id=None))


@webhook_router.get(
    "/webhooks/github/test",
    response_model=APIResponse[GitHubWebhookTestResponse],
    summary="Test webhook configuration",
    description="Test webhook configuration and connectivity.",
)
def test_webhook() -> APIResponse[GitHubWebhookTestResponse]:
    from socialseed_tasker.core.services.secret_manager import get_webhook_secret

    webhook_secret = get_webhook_secret()

    if not webhook_secret:
        return APIResponse(
            data=GitHubWebhookTestResponse(
                success=False,
                message="GITHUB_WEBHOOK_SECRET not configured",
            ),
            meta=Meta(request_id=None),
        )

    return APIResponse(
        data=GitHubWebhookTestResponse(
            success=True,
            message="Webhook configuration valid",
        ),
        meta=Meta(request_id=None),
    )


# In-memory agent storage for swarm coordination
_agents: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Agent router
# ---------------------------------------------------------------------------

agent_router = APIRouter()


@agent_router.post(
    "/agents/register",
    response_model=APIResponse[AgentResponse],
    status_code=201,
    summary="Register an agent",
    description="Register a new agent in the swarm coordination system.",
)
def register_agent(
    body: AgentRegisterRequest,
) -> APIResponse[AgentResponse]:
    from datetime import datetime, timezone

    agent_data = {
        "agent_id": body.agent_id,
        "name": body.name,
        "role": body.role,
        "status": "idle",
        "current_issue_id": None,
        "capabilities": body.capabilities,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_heartbeat": datetime.now(timezone.utc).isoformat(),
    }
    _agents[body.agent_id] = agent_data

    return APIResponse(
        data=AgentResponse(
            agent_id=body.agent_id,
            name=body.name,
            role=body.role,
            status="idle",
            current_issue_id=None,
            capabilities=body.capabilities,
            created_at=agent_data["created_at"],
            last_heartbeat=agent_data["last_heartbeat"],
        ),
        meta=Meta(request_id=None),
    )


@agent_router.get(
    "/agents",
    response_model=APIResponse[list[AgentResponse]],
    summary="List agents",
    description="List all registered agents.",
)
def list_agents() -> APIResponse[list[AgentResponse]]:
    from datetime import datetime, timezone

    agents = []
    for agent_data in _agents.values():
        agents.append(
            AgentResponse(
                agent_id=agent_data["agent_id"],
                name=agent_data["name"],
                role=agent_data["role"],
                status=agent_data["status"],
                current_issue_id=agent_data["current_issue_id"],
                capabilities=agent_data["capabilities"],
                created_at=agent_data["created_at"],
                last_heartbeat=agent_data["last_heartbeat"],
            )
        )
    return APIResponse(data=agents, meta=Meta(request_id=None))


@agent_router.get(
    "/agents/{agent_id}",
    response_model=APIResponse[AgentResponse],
    summary="Get agent",
    description="Get details of a specific agent.",
)
def get_agent(agent_id: str) -> APIResponse[AgentResponse]:
    from datetime import datetime, timezone

    if agent_id not in _agents:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    agent_data = _agents[agent_id]
    return APIResponse(
        data=AgentResponse(
            agent_id=agent_data["agent_id"],
            name=agent_data["name"],
            role=agent_data["role"],
            status=agent_data["status"],
            current_issue_id=agent_data["current_issue_id"],
            capabilities=agent_data["capabilities"],
            created_at=agent_data["created_at"],
            last_heartbeat=agent_data["last_heartbeat"],
        ),
        meta=Meta(request_id=None),
    )


@agent_router.post(
    "/agents/{agent_id}/heartbeat",
    response_model=APIResponse[AgentResponse],
    summary="Agent heartbeat",
    description="Update agent heartbeat and status.",
)
def agent_heartbeat(
    agent_id: str,
    body: AgentUpdateRequest,
) -> APIResponse[AgentResponse]:
    from datetime import datetime, timezone

    if agent_id not in _agents:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    agent_data = _agents[agent_id]
    if body.status:
        agent_data["status"] = body.status
    if body.current_issue_id is not None:
        agent_data["current_issue_id"] = body.current_issue_id
    agent_data["last_heartbeat"] = datetime.now(timezone.utc).isoformat()

    return APIResponse(
        data=AgentResponse(
            agent_id=agent_data["agent_id"],
            name=agent_data["name"],
            role=agent_data["role"],
            status=agent_data["status"],
            current_issue_id=agent_data["current_issue_id"],
            capabilities=agent_data["capabilities"],
            created_at=agent_data["created_at"],
            last_heartbeat=agent_data["last_heartbeat"],
        ),
        meta=Meta(request_id=None),
    )


@agent_router.delete(
    "/agents/{agent_id}",
    response_model=APIResponse[dict],
    summary="Deregister agent",
    description="Deregister an agent from the swarm.",
)
def deregister_agent(agent_id: str) -> APIResponse[dict]:
    if agent_id not in _agents:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    del _agents[agent_id]
    return APIResponse(data={"deleted": agent_id}, meta=Meta(request_id=None))


@agent_router.get(
    "/agents/role/{role}",
    response_model=APIResponse[list[AgentResponse]],
    summary="List agents by role",
    description="List all agents with a specific role.",
)
def list_agents_by_role(role: str) -> APIResponse[list[AgentResponse]]:
    from datetime import datetime, timezone

    agents = []
    for agent_data in _agents.values():
        if agent_data["role"] == role:
            agents.append(
                AgentResponse(
                    agent_id=agent_data["agent_id"],
                    name=agent_data["name"],
                    role=agent_data["role"],
                    status=agent_data["status"],
                    current_issue_id=agent_data["current_issue_id"],
                    capabilities=agent_data["capabilities"],
                    created_at=agent_data["created_at"],
                    last_heartbeat=agent_data["last_heartbeat"],
                )
            )
    return APIResponse(data=agents, meta=Meta(request_id=None))


# ---------------------------------------------------------------------------
# Admin router
# ---------------------------------------------------------------------------

admin_router = APIRouter()


def require_admin_auth(request: Request):
    """Require admin authentication for protected endpoints."""
    import os
    from fastapi import HTTPException

    admin_api_key = os.getenv("TASKER_ADMIN_API_KEY")
    if not admin_api_key:
        admin_api_key = os.getenv("TASKER_API_KEY", "")

    if not admin_api_key:
        raise HTTPException(
            status_code=500,
            detail="Admin authentication not configured",
        )

    provided_key = request.headers.get("X-API-Key")
    if provided_key != admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing admin API key",
        )


@admin_router.post(
    "/admin/reset",
    response_model=APIResponse[dict[str, Any]],
    summary="Reset data",
    description="Clear all or partial data from the database. Use with caution in production.",
    dependencies=[Depends(require_admin_auth)],
)
def reset_data(
    scope: str = Query("all", description="What to reset: 'all', 'issues', or 'components'"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    result = reset_data_action(repo, scope=scope)
    return APIResponse(data=result, meta=Meta(request_id=None))


# ---------------------------------------------------------------------------
# Sync router
# ---------------------------------------------------------------------------

sync_router = APIRouter()


@sync_router.get(
    "/status",
    response_model=APIResponse[dict],
    summary="Get sync status",
    description="Get current sync status (online/offline, queue size).",
)
def get_sync_status() -> APIResponse[dict]:
    from socialseed_tasker.core.services.sync_engine import get_sync_engine

    engine = get_sync_engine()
    engine.check_connectivity()
    status = engine.get_status()

    return APIResponse(data=status, meta=Meta(request_id=None))


@sync_router.get(
    "/queue",
    response_model=APIResponse[list[dict]],
    summary="Get sync queue",
    description="View pending sync queue items.",
)
def get_sync_queue() -> APIResponse[list[dict]]:
    from socialseed_tasker.core.services.sync_engine import get_sync_engine

    engine = get_sync_engine()
    queue = engine.get_queue()

    items = [
        {
            "id": str(item.id),
            "operation": item.operation.value,
            "entity_type": item.entity_type.value,
            "entity_id": str(item.entity_id),
            "status": item.status.value,
            "retry_count": item.retry_count,
            "created_at": item.created_at.isoformat(),
        }
        for item in queue
    ]

    return APIResponse(data=items, meta=Meta(request_id=None))


@sync_router.post(
    "/force",
    response_model=APIResponse[dict],
    summary="Force sync",
    description="Force a sync attempt to process the queue.",
)
def force_sync() -> APIResponse[dict]:
    from socialseed_tasker.core.services.sync_engine import get_sync_engine

    engine = get_sync_engine()
    engine.check_connectivity()
    result = engine.process_queue()

    return APIResponse(data=result, meta=Meta(request_id=None))


# ---------------------------------------------------------------------------
# Constraints router
# ---------------------------------------------------------------------------

constraints_router = APIRouter()


@constraints_router.post(
    "",
    response_model=APIResponse[ConstraintLoadResponse],
    summary="Load constraints from config",
    description="Load constraints from a YAML config file and store in Neo4j.",
)
def load_constraints(
    config: dict,
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[ConstraintLoadResponse]:
    from socialseed_tasker.core.task_management.constraints import ConstraintConfig
    from socialseed_tasker.core.task_management.actions import load_constraints_from_config_action

    constraint_config = ConstraintConfig(**config)
    result = load_constraints_from_config_action(repo, constraint_config)

    return APIResponse(
        data=ConstraintLoadResponse(**result),
        meta=Meta(request_id=None),
    )


@constraints_router.get(
    "",
    response_model=APIResponse[list[ConstraintResponse]],
    summary="List constraints",
    description="List all constraints, optionally filtered by category.",
)
def list_constraints(
    category: str | None = Query(None, description="Filter by category"),
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[list[ConstraintResponse]]:
    from socialseed_tasker.core.task_management.actions import list_constraints_action

    constraints = list_constraints_action(repo, category=category)

    return APIResponse(
        data=[
            ConstraintResponse(
                id=str(c.id),
                category=c.category.value,
                level=c.level.value,
                pattern=c.pattern,
                service=c.service,
                target=c.target,
                from_layer=c.from_layer,
                to_layer=c.to_layer,
                rule_type=c.rule_type,
                max_depth=c.max_depth,
                required=c.required,
                description=c.description,
                status=c.status.value,
            )
            for c in constraints
        ],
        meta=Meta(request_id=None),
    )


@constraints_router.get(
    "/validate",
    response_model=APIResponse[ConstraintValidationResponse],
    summary="Validate constraints",
    description="Validate all active constraints against current project state.",
)
def validate_constraints(
    repo: TaskRepositoryInterface = Depends(get_repo),
) -> APIResponse[ConstraintValidationResponse]:
    from socialseed_tasker.core.task_management.actions import validate_constraints_action

    result = validate_constraints_action(repo)

    return APIResponse(
        data=ConstraintValidationResponse(
            is_valid=result.is_valid,
            violations=[
                ConstraintViolationResponse(
                    constraint_id=str(v.constraint_id),
                    constraint_description=v.constraint_description,
                    level=v.level.value,
                    category=v.category.value,
                    affected_resource=v.affected_resource,
                    message=v.message,
                    suggestion=v.suggestion,
                )
                for v in result.violations
            ],
            hard_violations_count=len(result.hard_violations),
            soft_violations_count=len(result.soft_violations),
        ),
        meta=Meta(request_id=None),
    )
