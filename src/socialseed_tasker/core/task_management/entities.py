from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, AliasChoices

def _now():
    return datetime.now(timezone.utc)

def to_camel(string: str) -> str:
    return "".join(word.capitalize() if i > 0 else word for i, word in enumerate(string.split("_")))

class ProjectVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"

class ProjectStatus(str, Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"

class GlobalStatus(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"

class IssueStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    CLOSED = "CLOSED"
    BLOCKED = "BLOCKED"

class IssuePriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class UserRole(str, Enum):
    ADMIN = "ADMIN"
    DEVELOPER = "DEVELOPER"
    VIEWER = "VIEWER"

class User(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    username: str = Field(..., min_length=1)
    email: Optional[str] = None
    role: UserRole = UserRole.DEVELOPER
    github_handle: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    last_login: Optional[datetime] = None
    preferences: Optional[str] = None

class DecisionType(str, Enum):
    SOLUTION_SELECTION = "solution_selection"
    ARCHITECTURE_CHOICE = "architecture_choice"
    PRIORITY_DECISION = "priority_decision"
    DEPENDENCY_RESOLUTION = "dependency_resolution"
    REFACTORING_CHOICE = "refactoring_choice"
    CODE_GENERATION = "code_generation"
    REVIEW_DECISION = "review_decision"
    UNKNOWN = "unknown"

class ReasoningContext(str, Enum):
    ARCHITECTURE_CHOICE = "architecture_choice"
    SOLUTION_DESIGN = "solution_design"
    REFACTORING = "refactoring"
    BUG_FIX = "bug_fix"
    TEST_PLAN = "test_plan"

class ReasoningLogEntry(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=_now)
    context: ReasoningContext = ReasoningContext.ARCHITECTURE_CHOICE
    reasoning: str = ""
    related_nodes: list[UUID] = Field(default_factory=list)

class Project(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    slug: str = Field(..., min_length=1)
    description: str = ""
    repository_url: Optional[str] = None
    base_package: Optional[str] = None
    visibility: ProjectVisibility = ProjectVisibility.PRIVATE
    status: ProjectStatus = ProjectStatus.ACTIVE
    tech_stack: list[str] = Field(default_factory=list)
    main_stack: list[str] = Field(default_factory=list)
    architecture_style: Optional[str] = None
    version: str = "0.0.1"
    conventions_url: Optional[str] = None
    conventions_rules: Optional[str] = None
    last_full_scan: Optional[datetime] = None
    global_status: GlobalStatus = GlobalStatus.DEVELOPMENT
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

class Component(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    project: str = Field(..., min_length=1)
    project_id: Optional[UUID] = None
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

class Label(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    color: Optional[str] = None
    description: str = ""
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

class Issue(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=1)
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
    closed_at: Optional[datetime] = None
    architectural_constraints: list[str] = Field(default_factory=list)
    agent_working: bool = False
    agent_started_at: Optional[datetime] = None
    agent_finished_at: Optional[datetime] = None
    agent_id: Optional[str] = None
    locked_until: Optional[datetime] = None
    reasoning_logs: list[ReasoningLogEntry] = Field(default_factory=list)
    manifest_todo: list[dict[str, str]] = Field(default_factory=list)
    manifest_files: list[str] = Field(default_factory=list)
    manifest_notes: list[str] = Field(default_factory=list)
    github_issue_url: Optional[str] = None
    github_issue_number: Optional[int] = None
    last_mirrored_at: Optional[datetime] = None
    estimated_hours: Optional[float] = None
    hourly_rate_tier: Optional[str] = None
    resolved_by_commit_sha: Optional[str] = Field(default=None, description="Git commit SHA that resolved this issue")
    resolution: Optional[str] = Field(default=None, description="Resolution type: implemented, duplicate, wontfix, etc.")
    actual_hours: Optional[float] = None
    epic_id: Optional[UUID] = None
    description_embedding: Optional[list[float]] = None

    def to_indexable_text(self) -> str:
        parts = [f"Issue: {self.title}", f"Description: {self.description}"]
        return "\n\n".join(parts)

class ReasoningNode(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    thought: str = Field(..., min_length=1)
    confidence: float = 0.5
    alternatives_considered: list[str] = Field(default_factory=list)
    rejected_reasons: list[str] = Field(default_factory=list)
    decision: Optional[str] = None
    decision_type: DecisionType = DecisionType.UNKNOWN
    created_at: datetime = Field(default_factory=_now)

class Commit(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    sha: str = Field(..., min_length=40, max_length=40)
    message: str = ""
    author_name: str = ""
    author_email: str = ""
    timestamp: datetime = Field(default_factory=_now)
    is_ai_generated: bool = False
    branch: str = ""
    additions: int = 0
    deletions: int = 0
    files_changed: int = 0

class ReasoningFeedback(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    reasoning_id: UUID = Field(...)
    is_approved: bool = Field(...)
    feedback_text: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    last_heartbeat: datetime = Field(default_factory=_now)


class AgentStatus(str, Enum):
    IDLE = "IDLE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"


class AgentRole(str, Enum):
    DEVELOPER = "DEVELOPER"
    TESTER = "TESTER"
    ARCHITECT = "ARCHITECT"
    PLANNER = "PLANNER"
    REVIEWER = "REVIEWER"
    OBSERVER = "OBSERVER"


class Agent(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    id: str = Field(..., description="Unique agent identifier")
    name: str = Field(..., min_length=1, max_length=100)
    role: AgentRole = AgentRole.DEVELOPER
    status: AgentStatus = AgentStatus.IDLE
    capabilities: list[str] = Field(default_factory=list)
    current_issue_id: Optional[str] = None
    created_at: datetime = Field(default_factory=_now)
    last_heartbeat: datetime = Field(default_factory=_now)


class EpicStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class Epic(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    description: str = ""
    objective_id: Optional[UUID] = None
    status: EpicStatus = EpicStatus.OPEN
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class ObjectiveStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class Objective(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    description: str = ""
    status: ObjectiveStatus = ObjectiveStatus.OPEN
    quarter: str = ""
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class DeploymentEnvironment(str, Enum):
    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class Deployment(BaseModel):
    model_config = ConfigDict(frozen=True, populate_by_name=True, alias_generator=to_camel)
    id: UUID = Field(default_factory=uuid4)
    commit_sha: str = Field(..., min_length=40, max_length=40)
    environment_name: DeploymentEnvironment = DeploymentEnvironment.DEVELOPMENT
    deployed_at: datetime = Field(default_factory=_now)
    issue_ids: list[UUID] = Field(default_factory=list)
    channel: str = "default"
    deployed_by: str = ""
