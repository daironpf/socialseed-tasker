"""API route definitions for issues, dependencies, components, and analysis.

All routes delegate to core actions - no business logic lives here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends, Query, Request  # noqa: B008

from socialseed_tasker.core.project_analysis.analyzer import (
    ComponentImpactAnalysis,
    ImpactAnalysis,
    RootCauseAnalyzer,
    TestFailure,
)
from socialseed_tasker.core.task_management.actions import (
    ComponentNotFoundError,
    IssueNotFoundError,
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
    ComponentResponse,
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
    TestFailureRequest,
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
    issue, warnings = create_issue_action(
        repo,
        title=body.title,
        component_id=body.component_id,
        description=body.description,
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
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
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
):
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
    response_model=APIResponse[list[IssueResponse]],
    summary="List dependencies",
    description="List all issues that this issue depends on.",
)
def list_dependencies(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    issue = repo.get_issue(issue_id)
    if issue is None:
        raise IssueNotFoundError(issue_id)
    deps = repo.get_dependencies(issue_id)
    return APIResponse(data=[_issue_to_response(d) for d in deps], meta=Meta(request_id=None))


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
    from socialseed_tasker.core.task_management.entities import Component

    comp = Component(name=body.name, description=body.description, project=body.project)
    repo.create_component(comp)
    return APIResponse(data=_component_to_response(comp), meta=Meta(request_id=None))


@components_router.get(
    "/components",
    response_model=APIResponse[list[ComponentResponse]],
    summary="List components",
    description="List all components, optionally filtered by project or name.",
)
def list_components(
    project: str | None = Query(None, description="Filter by project"),
    name: str | None = Query(None, description="Filter by exact name"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    if name:
        comp = repo.get_component_by_name(name, project)
        components = [comp] if comp else []
    else:
        components = repo.list_components(project=project)
    return APIResponse(data=[_component_to_response(c) for c in components], meta=Meta(request_id=None))


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
# Admin router
# ---------------------------------------------------------------------------

admin_router = APIRouter()


@admin_router.post(
    "/admin/reset",
    response_model=APIResponse[dict[str, Any]],
    summary="Reset data",
    description="Clear all or partial data from the database. Use with caution in production.",
)
def reset_data(
    scope: str = Query("all", description="What to reset: 'all', 'issues', or 'components'"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    result = reset_data_action(repo, scope=scope)
    return APIResponse(data=result, meta=Meta(request_id=None))
