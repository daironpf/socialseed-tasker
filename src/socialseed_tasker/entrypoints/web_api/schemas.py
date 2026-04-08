"""Pydantic schemas for API request/response models.

All request bodies and responses use these models for validation
and consistent envelope formatting.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Envelope models
# ---------------------------------------------------------------------------


class ErrorDetail(BaseModel):
    """Structured error information."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context about the error",
    )


class Meta(BaseModel):
    """Response metadata."""

    model_config = {"populate_by_name": True}

    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response generation timestamp",
    )
    request_id: str | None = Field(
        default=None,
        description="Unique request identifier for tracing",
    )
    warnings: list[str] | None = Field(
        default=None,
        description="Non-critical warnings for the client",
    )


class APIResponse(BaseModel, Generic[T]):
    """Standard response envelope for all API endpoints.

    Intent: Provide a consistent structure so AI agents can always
    parse responses the same way.
    Business Value: Simplifies client code and enables generic response
    handling across all endpoints.
    """

    data: T | None = Field(None, description="The response payload")
    error: ErrorDetail | None = Field(
        default=None,
        description="Error information (present only on failure)",
    )
    meta: Meta = Field(default_factory=Meta, description="Response metadata")


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------


class PaginationMeta(BaseModel):
    """Pagination information for list endpoints."""

    page: int = Field(..., ge=1, description="Current page number")
    limit: int = Field(..., ge=1, le=100, description="Items per page")
    total: int = Field(..., ge=0, description="Total number of items")
    has_next: bool = Field(..., description="Whether a next page exists")
    has_prev: bool = Field(..., description="Whether a previous page exists")


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated response envelope."""

    items: list[T] = Field(default_factory=list)
    pagination: PaginationMeta


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class IssueCreateRequest(BaseModel):
    """Request body for creating a new issue."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Issue title",
        examples=["Fix login authentication bug"],
    )
    description: str = Field(
        "",
        description="Detailed description in Markdown",
        examples=["Users receive a 500 error when submitting valid credentials"],
    )
    priority: str = Field(
        "MEDIUM",
        description="Priority level: LOW, MEDIUM, HIGH, CRITICAL",
        examples=["HIGH"],
    )
    component_id: str | None = Field(
        None,
        description="UUID of the component this issue belongs to. If not provided, issue will be created in 'uncategorized' component.",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )
    labels: list[str] = Field(
        default_factory=list,
        description="Tags for categorisation",
        examples=[["bug", "auth", "urgent"]],
    )
    architectural_constraints: list[str] = Field(
        default_factory=list,
        description="Architectural rules this issue must comply with",
        examples=["no-sql-in-graph-module"],
    )


class IssueUpdateRequest(BaseModel):
    """Request body for partially updating an issue."""

    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    component_id: str | None = None
    labels: list[str] | None = None
    architectural_constraints: list[str] | None = None
    agent_working: bool | None = None


class DependencyRequest(BaseModel):
    """Request body for adding a dependency."""

    depends_on_id: str = Field(
        ...,
        description="UUID of the issue this issue depends on",
        examples=["550e8400-e29b-41d4-a716-446655440000"],
    )


class BulkDependencyRequest(BaseModel):
    """Request body for adding multiple dependencies at once."""

    depends_on_ids: list[str] = Field(
        ...,
        min_length=1,
        max_length=50,
        description="List of UUIDs this issue depends on",
        examples=[["550e8400-e29b-41d4-a716-446655440000", "660e8400-e29b-41d4-a716-446655440001"]],
    )


class BulkDependencyResponse(BaseModel):
    """Response for bulk dependency creation."""

    issue_id: str
    total_requested: int
    successful: int
    failed: int
    results: list[dict[str, Any]]


class ComponentCreateRequest(BaseModel):
    """Request body for creating a new component."""

    name: str = Field(
        ...,
        min_length=1,
        description="Component name",
        examples=["Backend"],
    )
    description: str | None = Field(
        None,
        description="Component description",
        examples=["REST API and business logic layer"],
    )
    project: str = Field(
        ...,
        min_length=1,
        description="Project this component belongs to",
        examples=["socialseed-tasker"],
    )


class TestFailureRequest(BaseModel):
    """Request body for submitting a test failure for root-cause analysis."""

    test_id: str = Field(..., description="Unique test identifier")
    test_name: str = Field(..., description="Test function/class name")
    error_message: str = Field(..., description="Error message from the test runner")
    stack_trace: str = Field("", description="Full stack trace")
    component: str = Field("", description="Component where the failure occurred")
    labels: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Response schemas (data payloads)
# ---------------------------------------------------------------------------


class IssueResponse(BaseModel):
    """Single issue in API responses."""

    id: str
    title: str
    description: str
    status: str
    priority: str
    component_id: str
    labels: list[str]
    dependencies: list[str]
    blocks: list[str]
    affects: list[str]
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    architectural_constraints: list[str]
    agent_working: bool | None = None


class ComponentResponse(BaseModel):
    """Single component in API responses."""

    id: str
    name: str
    description: str | None
    project: str
    created_at: datetime
    updated_at: datetime


class DependencyResponse(BaseModel):
    """Dependency relationship information."""

    issue_id: str
    depends_on_id: str


class CausalLinkResponse(BaseModel):
    """Root-cause analysis result linking a test failure to an issue."""

    issue_id: str
    issue_title: str
    confidence: float
    reasons: list[str]
    graph_distance: int


class ImpactIssueSummary(BaseModel):
    """Summary of an issue in impact analysis."""

    id: str
    title: str
    status: str


class ImpactAnalysisResponse(BaseModel):
    """Impact analysis result for an issue."""

    issue_id: str
    directly_affected: list[ImpactIssueSummary]
    transitively_affected: list[ImpactIssueSummary]
    blocked_issues: list[ImpactIssueSummary]
    affected_components: list[str]
    risk_level: str


class ComponentImpactIssueSummary(BaseModel):
    """Summary of an issue within component impact analysis."""

    id: str
    title: str
    status: str


class ComponentImpactAnalysisResponse(BaseModel):
    """Impact analysis result for an entire component."""

    component_id: str
    component_name: str
    total_issues: int
    directly_affected_components: list[str]
    transitively_affected_components: list[str]
    total_blocked_issues: int
    criticality_score: int
    risk_level: str
    affected_issues_summary: list[ComponentImpactIssueSummary]


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = "healthy"
    version: str = "0.5.0"
    storage_backend: str = "neo4j"


class GraphNode(BaseModel):
    """Node in the dependency graph."""

    id: str
    title: str
    component: str | None = None
    status: str
    priority: str


class GraphEdge(BaseModel):
    """Edge in the dependency graph."""

    from_node: str
    to_node: str


class DependencyGraphResponse(BaseModel):
    """Full dependency graph for the project."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class ProjectSummaryResponse(BaseModel):
    """Summary dashboard for a project."""

    project: str
    total_issues: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    components_count: int
    blocked_issues_count: int
    workable_issues_count: int
    dependency_health: float
    top_blocked_components: list[dict[str, int]]
    critical_path_length: int
