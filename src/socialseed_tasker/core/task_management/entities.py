"""Core domain entities - Issue and Component.

These entities form the domain model that powers the entire task management system.
They encode the graph relationships (dependencies, blocks, affects) that enable
causal traceability and architectural integrity checks.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


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
    description: Optional[str] = None
    project: str = Field(..., min_length=1)
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
    closed_at: Optional[datetime] = None
    architectural_constraints: list[str] = Field(default_factory=list)
