"""Core domain entities - Issue and Component.

These entities form the domain model that powers the entire task management system.
They encode the graph relationships (dependencies, blocks, affects) that enable
causal traceability and architectural integrity checks.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from socialseed_tasker.core.task_management.value_objects import ReasoningLogEntry


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class ProjectStatus(str, Enum):
    """Lifecycle states for a Project.

    Intent: Define the possible states a project can be in during its lifecycle.
    Business Value: Enables project filtering (e.g., find all active projects).
    """

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DEMO = "DEMO"


class ProjectVisibility(str, Enum):
    """Visibility levels for a Project.

    Intent: Classify projects by their accessibility.
    Business Value: Drives rendering rules in multi-tenant systems.
    """

    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


class GlobalStatus(str, Enum):
    """Global deployment status for a Project.

    Intent: Track the current deployment environment/state.
    Business Value: Enables governance checks and deployment gating.
    """

    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class Project(BaseModel):
    """A software project being managed by the task system.

    Intent: Represent a root-level container that holds architectural
    context, governance rules, and global configuration for all
    components and issues within it.
    Business Value: Enables AI agents to understand global architectural
    context, follow project-specific conventions, and perform cross-component
    analysis with high precision.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, description="Official project name")
    slug: str = Field(..., min_length=1, description="URL-friendly identifier")
    description: str = ""
    repository_url: str | None = None
    base_package: str | None = None
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE
    status: ProjectStatus = ProjectStatus.ACTIVE
    tech_stack: list[str] = Field(default_factory=list)
    main_stack: list[str] = Field(default_factory=list)
    architecture_style: str | None = None
    version: str = "0.0.1"
    conventions_url: str | None = None
    conventions_rules: str | None = None
    last_full_scan: datetime | None = None
    global_status: GlobalStatus = GlobalStatus.DEVELOPMENT
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class IssueStatus(str, Enum):
    """Lifecycle states for an Issue.

    Intent: Define the possible states an issue can be in during its lifecycle.
    Business Value: Enables workflow tracking and filtering (e.g., find all blocked issues).
    """

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    BLOCKED = "BLOCKED"


class IssuePriority(str, Enum):
    """Priority levels for an Issue.

    Intent: Classify issues by urgency so teams can focus on what matters most.
    Business Value: Drives triage, sprint planning, and automated escalation rules.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Component(BaseModel):
    """A logical component or module within a project.

    Intent: Group related issues under a named component so the system can
    enforce architectural rules and produce scoped reports.
    Business Value: Provides a boundary for dependency analysis and
    architectural-integrity checks across different parts of a project.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    description: str | None = None
    project: str = Field(..., min_length=1, description="Project name (for backward compatibility)")
    project_id: UUID | None = Field(default=None, description="Project UUID reference")
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Label(BaseModel):
    """A label for categorizing issues.

    Intent: Provide semantic categorization for issues
    so agents can filter and prioritize based on tags.
    Business Value: Enables issue filtering and domain grouping.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    color: str | None = None
    description: str = ""
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Issue(BaseModel):
    """A task or issue in the graph-based task management system.

    Intent: Represent a unit of work that can be tracked, linked, and analysed
    through a dependency graph.
    Business Value: Encodes relationships (DEPENDS_ON, BLOCKS, AFFECTS) that
    power root-cause analysis, impact assessment, and architectural governance.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    status: IssueStatus = IssueStatus.OPEN
    priority: IssuePriority = IssuePriority.MEDIUM
    component_id: UUID = Field(...)
    labels: list[str] = Field(default_factory=list)
    dependencies: list[UUID] = Field(default_factory=list)
    blocks: list[UUID] = Field(default_factory=list)
    affects: list[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)
    closed_at: datetime | None = None
    architectural_constraints: list[str] = Field(default_factory=list)
    agent_working: bool = False
    agent_started_at: datetime | None = None
    agent_finished_at: datetime | None = None
    agent_id: str | None = None
    locked_until: datetime | None = None
    reasoning_logs: list[ReasoningLogEntry] = Field(default_factory=list)
    manifest_todo: list[dict[str, str]] = Field(default_factory=list)
    manifest_files: list[str] = Field(default_factory=list)
    manifest_notes: list[str] = Field(default_factory=list)
    github_issue_url: str | None = None
    github_issue_number: int | None = None
    last_mirrored_at: datetime | None = None
    estimated_hours: float | None = None
    hourly_rate_tier: str | None = None
    actual_hours: float | None = None
    epic_id: UUID | None = None
    description_embedding: list[float] | None = None

    def to_indexable_text(self) -> str:
        """Combine fields into a single text block for semantic indexing.

        Business Value: Enables AI agents to find this issue via semantic search
        by providing a rich text representation of the problem and its solution.
        """
        parts = [f"Issue: {self.title}", f"Description: {self.description}"]
        if self.manifest_notes:
            parts.append(f"Technical Notes: {' '.join(self.manifest_notes)}")
        if self.manifest_todo:
            todos = [t.get("task", "") for t in self.manifest_todo if isinstance(t, dict)]
            parts.append(f"Work performed: {' '.join(todos)}")
        if self.labels:
            parts.append(f"Labels: {', '.join(self.labels)}")
        return "\n\n".join(parts)


class HourlyRateTier(str, Enum):
    JUNIOR = "JUNIOR"
    SENIOR = "SENIOR"
    STAFF = "STAFF"
    PRINCIPAL = "PRINCIPAL"


class EpicStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class ObjectiveStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class EnvironmentType(str, Enum):
    """Environment types for deployment tracking."""

    PROD = "PROD"
    STAGING = "STAGING"
    DEV = "DEV"
    QA = "QA"


class Environment(BaseModel):
    """Deployment environment."""

    id: UUID
    name: EnvironmentType
    url: str | None = None
    is_active: bool = True


class Deployment(BaseModel):
    """A deployment event."""

    id: UUID
    commit_sha: str
    environment_name: EnvironmentType
    deployed_at: datetime
    issue_ids: list[UUID]
    channel: str | None = None
    deployed_by: str | None = None


class Epic(BaseModel):
    """Group of issues that share a common initiative."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    objective_id: UUID | None = None
    status: EpicStatus = EpicStatus.OPEN
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class Objective(BaseModel):
    """Strategic objective (OKR) that Epics contribute to."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    status: ObjectiveStatus = ObjectiveStatus.OPEN
    quarter: str = ""
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class AgentRole(str, Enum):
    """Roles for multi-agent coordination.

    Intent: Define specialized responsibilities for different AI agents.
    Business Value: Enables coordinated workflows where agents specialize
    in planning, development, and review.
    """

    PLANNER = "planner"
    DEVELOPER = "developer"
    REVIEWER = "reviewer"
    OBSERVER = "observer"


class AgentStatus(str, Enum):
    """Status of an agent in the swarm."""

    IDLE = "idle"
    WORKING = "working"
    BLOCKED = "blocked"
    OFFLINE = "offline"


class Agent(BaseModel):
    """An AI agent in the swarm coordination system.

    Intent: Represent an AI agent with specific role and capabilities
    for coordinated multi-agent work.
    Business Value: Enables role-based work distribution and
    inter-agent coordination.
    """

    model_config = ConfigDict(frozen=True)

    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., min_length=1, max_length=100)
    role: AgentRole = AgentRole.DEVELOPER
    status: AgentStatus = AgentStatus.IDLE
    current_issue_id: str | None = None
    capabilities: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)


class DecisionType(str, Enum):
    """Types of reasoning decisions."""

    SOLUTION_SELECTION = "solution_selection"
    ARCHITECTURE_CHOICE = "architecture_choice"
    PRIORITY_DECISION = "priority_decision"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    REFACTORING_CHOICE = "refactoring_choice"
    CODE_GENERATION = "code_generation"
    REVIEW_DECISION = "review_decision"
    UNKNOWN = "unknown"


class ReasoningNode(BaseModel):
    """Records agent reasoning for transparency and learning.

    Pattern: (Agent)-[:THOUGHT]->(ReasoningNode)-[:DECIDED]->(Issue)
    """

    id: UUID = Field(default_factory=lambda: str(uuid4()))
    thought: str = Field(..., min_length=1, description="The agent's reasoning text")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    alternatives_considered: list[str] = Field(default_factory=list, description="Options evaluated")
    rejected_reasons: list[str] = Field(default_factory=list, description="Why alternatives were rejected")
    decision: str | None = Field(default=None, description="The decision made")
    decision_type: DecisionType = DecisionType.UNKNOWN
    created_at: datetime = Field(default_factory=_now)


class ReasoningFeedback(BaseModel):
    """Human feedback on agent reasoning."""

    id: UUID = Field(default_factory=lambda: str(uuid4()))
    reasoning_id: UUID = Field(..., description="The reasoning node being feedbacked")
    is_approved: bool = Field(..., description="True for approval, False for disapproval")
    feedback_text: str | None = None
    created_at: datetime = Field(default_factory=_now)
    last_heartbeat: datetime = Field(default_factory=_now)
