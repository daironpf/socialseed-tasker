"""Value objects used across the task management domain."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class ReasoningContext(str, Enum):
    """Context types for reasoning log entries.

    Intent: Categorize the type of reasoning being recorded.
    Business Value: Enables filtering and analysis of reasoning by context.
    """

    COMPONENT_SELECTION = "component_selection"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    ARCHITECTURE_CHOICE = "architecture_choice"
    IMPACT_ASSESSMENT = "impact_assessment"
    PRIORITY_DECISION = "priority_decision"


class ReasoningLogEntry(BaseModel):
    """A single reasoning log entry attached to an issue.

    Intent: Capture the AI's decision-making process for transparency
    and auditability.
    Business Value: Enables human reviewers to understand and validate
    architectural choices made by autonomous agents.
    """

    model_config = {"frozen": True}

    id: UUID = Field(default_factory=uuid4)
    timestamp: datetime = Field(default_factory=_now)
    context: ReasoningContext = Field(..., description="Type of reasoning")
    reasoning: str = Field(..., min_length=1, description="Explanation of the decision")
    related_nodes: list[UUID] = Field(
        default_factory=list,
        description="Related issue/component IDs",
    )
