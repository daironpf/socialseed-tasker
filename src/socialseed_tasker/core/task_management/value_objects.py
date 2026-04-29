"""Value objects used across the task management domain."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


def _now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(timezone.utc)


class HourlyRateTier(str, Enum):
    """Hourly rate tiers for cost attribution.

    Intent: Standardize billing rates for enterprise accounting.
    Business Value: Enables Capitalized Software Development tracking.
    """

    JUNIOR = "JUNIOR"
    SENIOR = "SENIOR"
    STAFF = "STAFF"
    PRINCIPAL = "PRINCIPAL"


HOURLY_RATES: dict[HourlyRateTier, float] = {
    HourlyRateTier.JUNIOR: 75.0,
    HourlyRateTier.SENIOR: 125.0,
    HourlyRateTier.STAFF: 175.0,
    HourlyRateTier.PRINCIPAL: 250.0,
}


def calculate_cost(hours: float | None, tier: str | None) -> float:
    """Calculate cost based on hours and rate tier.

    Args:
        hours: Actual or estimated hours
        tier: HourlyRateTier value

    Returns:
        Total cost in dollars
    """
    if hours is None or tier is None:
        return 0.0
    rate = HOURLY_RATES.get(HourlyRateTier(tier), 0.0)
    return hours * rate


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
