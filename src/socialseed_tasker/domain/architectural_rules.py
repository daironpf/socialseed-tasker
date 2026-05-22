"""Architectural rules and integrity constraints.

Defines rule types, severity levels, and the ArchitecturalRule entity
used for enforcing architectural governance across projects.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RuleType(str, Enum):
    """Types of architectural rules.

    Intent: Categorise the kinds of architectural constraints that can
    be enforced against issues and their relationships.
    Business Value: Enables flexible governance policies that evolve
    with the project's needs.
    """

    FORBIDDEN_DEPENDENCY = "FORBIDDEN_DEPENDENCY"
    FORBIDDEN_TECHNOLOGY = "FORBIDDEN_TECHNOLOGY"
    REQUIRED_PATTERN = "REQUIRED_PATTERN"
    MAX_DEPENDENCY_DEPTH = "MAX_DEPENDENCY_DEPTH"


class Severity(str, Enum):
    """Severity levels for rule violations.

    Intent: Distinguish between violations that must block an action
    (ERROR) and those that merely warn the user (WARNING).
    Business Value: Allows teams to enforce critical rules strictly
    while keeping advisory rules as informational warnings.
    """

    ERROR = "ERROR"
    WARNING = "WARNING"


class ArchitecturalRule(BaseModel):
    """A rule that governs architectural integrity.

    Intent: Encode architectural decisions as machine-checkable rules
    so the system can prevent violations before they occur.
    Business Value: Prevents architectural degradation over time by
    automatically validating actions against established patterns.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    description: str = ""
    rule_type: RuleType
    source_pattern: str = Field(
        "",
        description="Component or label pattern to match as the source",
    )
    target_pattern: str = Field(
        "",
        description="Component or label pattern to check against",
    )
    severity: Severity = Severity.ERROR
    is_active: bool = True
    max_depth: int = Field(
        5,
        description="Maximum allowed dependency depth (for MAX_DEPENDENCY_DEPTH)",
        ge=1,
    )
    created_at: datetime = Field(default_factory=_now)


class Violation(BaseModel):
    """A single rule violation found during analysis."""

    rule_id: UUID
    rule_name: str
    severity: Severity
    message: str
    suggestion: str = ""


class ValidationResult(BaseModel):
    """Result of evaluating architectural rules against an action.

    Intent: Provide a structured report of all violations found so
    the caller can decide whether to proceed or abort.
    Business Value: Enables consistent handling of violations across
    CLI, API, and agent interfaces.
    """

    violations: list[Violation] = Field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.violations) == 0

    @property
    def has_errors(self) -> bool:
        return any(v.severity == Severity.ERROR for v in self.violations)

    @property
    def has_warnings(self) -> bool:
        return any(v.severity == Severity.WARNING for v in self.violations)
