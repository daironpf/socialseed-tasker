"""API route definitions for issues, dependencies, components, and analysis.

All routes delegate to core actions - no business logic lives here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, Query, Request  # noqa: B008

from socialseed_tasker.core.project_analysis.analyzer import (
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
    remove_dependency_action,
)
from socialseed_tasker.core.task_management.entities import IssueStatus
from socialseed_tasker.entrypoints.web_api.schemas import (
    APIResponse,
    CausalLinkResponse,
    ComponentCreateRequest,
    ComponentResponse,
    DependencyRequest,
    DependencyResponse,
    ImpactAnalysisResponse,
    ImpactIssueSummary,
    IssueCreateRequest,
    IssueResponse,
    IssueUpdateRequest,
    Meta,
    PaginatedResponse,
    PaginationMeta,
    TestFailureRequest,
)

if TYPE_CHECKING:
    pass


class RepositoryDependency:
    """FastAPI dependency that provides the task repository from app state."""

    def __call__(self, request: Request) -> TaskRepositoryInterface:
        return request.app.state.repository


get_repo = RepositoryDependency()


def _issue_to_response(issue) -> IssueResponse:
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
    )


def _component_to_response(comp) -> ComponentResponse:
    """Convert a domain Component to an API response model."""
    return ComponentResponse(
        id=str(comp.id),
        name=comp.name,
        description=comp.description,
        project=comp.project,
        created_at=comp.created_at,
        updated_at=comp.updated_at,
    )


def _paginated(items, page: int, limit: int, total: int) -> PaginatedResponse:
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
):
    issue = create_issue_action(
        repo,
        title=body.title,
        component_id=body.component_id,
        description=body.description,
        priority=body.priority,
        labels=body.labels,
        architectural_constraints=body.architectural_constraints,
    )
    return APIResponse(data=_issue_to_response(issue), meta=Meta())


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
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    status_filter = IssueStatus(status) if status else None
    all_issues = repo.list_issues(component_id=component, status=status_filter)
    total = len(all_issues)
    start = (page - 1) * limit
    end = start + limit
    page_items = all_issues[start:end]

    return APIResponse(
        data=_paginated([_issue_to_response(i) for i in page_items], page, limit, total),
        meta=Meta(),
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
    return APIResponse(data=_issue_to_response(issue), meta=Meta())


@issues_router.patch(
    "/issues/{issue_id}",
    response_model=APIResponse[IssueResponse],
    summary="Update an issue",
    description="Partially update an issue's fields.",
    responses={404: {"description": "Issue not found"}},
)
def update_issue(
    issue_id: str,
    body: IssueUpdateRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    existing = repo.get_issue(issue_id)
    if existing is None:
        raise IssueNotFoundError(issue_id)

    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return APIResponse(data=_issue_to_response(existing), meta=Meta())

    updated = repo.update_issue(issue_id, updates)
    return APIResponse(data=_issue_to_response(updated), meta=Meta())


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
    return APIResponse(data=_issue_to_response(issue), meta=Meta())


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
        meta=Meta(),
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
    return APIResponse(data=[_issue_to_response(d) for d in deps], meta=Meta())


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
    return APIResponse(data=[_issue_to_response(d) for d in dependents], meta=Meta())


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
    return APIResponse(data=[_issue_to_response(i) for i in chain], meta=Meta())


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
    return APIResponse(data=[_issue_to_response(i) for i in blocked], meta=Meta())


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
    return APIResponse(data=_component_to_response(comp), meta=Meta())


@components_router.get(
    "/components",
    response_model=APIResponse[list[ComponentResponse]],
    summary="List components",
    description="List all components, optionally filtered by project.",
)
def list_components(
    project: str | None = Query(None, description="Filter by project"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    components = repo.list_components(project=project)
    return APIResponse(data=[_component_to_response(c) for c in components], meta=Meta())


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
    return APIResponse(data=_component_to_response(comp), meta=Meta())


@components_router.patch(
    "/components/{component_id}",
    response_model=APIResponse[ComponentResponse],
    summary="Update a component",
    description="Update one or more fields of a component.",
)
def update_component(
    component_id: str,
    body: dict,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    from socialseed_tasker.core.task_management.actions import update_component_action

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
        return APIResponse(data=_component_to_response(updated), meta=Meta())
    except FileNotFoundError:
        raise ComponentNotFoundError(component_id)
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(e))


@components_router.delete(
    "/components/{component_id}",
    response_model=APIResponse[dict],
    summary="Delete a component",
    description="Delete a component. Fails if component has issues unless force=true.",
)
def delete_component(
    component_id: str,
    force: bool = Query(False, description="Force deletion even if component has issues"),
    repo: TaskRepositoryInterface = Depends(get_repo),
):
    from socialseed_tasker.core.task_management.actions import delete_component_action, ComponentHasIssuesError

    try:
        delete_component_action(repo, component_id, force=force)
        return APIResponse(data={"deleted": component_id}, meta=Meta())
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
    response_model=APIResponse[list],
    summary="Find root cause of test failure",
    description=(
        "Submit a test failure and get potential root causes ranked by "
        "confidence. Uses graph proximity analysis to link failed tests "
        "to recently closed issues."
    ),
)
def analyze_root_cause(
    body: TestFailureRequest,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
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
    return APIResponse(data=link_data, meta=Meta())


@analysis_router.get(
    "/analyze/impact/{issue_id}",
    response_model=APIResponse[ImpactAnalysisResponse],
    summary="Get impact analysis",
    description="Analyse what other issues and components would be affected.",
)
def analyze_impact(
    issue_id: str,
    repo: TaskRepositoryInterface = Depends(get_repo),
):
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
    return APIResponse(data=impact_data, meta=Meta())
