"""Constraint domain entities.

Defines the core constraint models for architectural governance.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ConstraintCategory(str, Enum):
    """Categories of constraints."""

    ARCHITECTURE = "architecture"
    TECHNOLOGY = "technology"
    NAMING = "naming"
    PATTERNS = "patterns"
    DEPENDENCIES = "dependencies"


class ConstraintLevel(str, Enum):
    """Enforcement level for constraints."""

    HARD = "hard"
    SOFT = "soft"


class ConstraintStatus(str, Enum):
    """Status of a constraint."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    VIOLATED = "violated"
    COMPLIANT = "compliant"


class ArchitectureConstraint(BaseModel):
    """Architecture pattern constraint."""

    model_config = ConfigDict(frozen=True)

    pattern: str = Field(..., description="Required or forbidden pattern")
    required: bool = Field(default=True, description="True for required, False for forbidden")
    description: str = ""


class TechnologyConstraint(BaseModel):
    """Technology constraint."""

    model_config = ConfigDict(frozen=True)

    service: str = Field(..., description="Service name or '*' for all")
    technology: str = Field(..., description="Technology name")
    required: bool = Field(default=True, description="True for required, False for forbidden")
    description: str = ""


class NamingConstraint(BaseModel):
    """Naming convention constraint."""

    model_config = ConfigDict(frozen=True)

    target: str = Field(..., description="Target: fields, classes, tables, prefixes")
    pattern: str = Field(..., description="Regex pattern or prefix")
    description: str = ""


class PatternConstraint(BaseModel):
    """Structural pattern constraint."""

    model_config = ConfigDict(frozen=True)

    pattern: str = Field(..., description="Pattern name")
    required: bool = Field(default=True, description="True for required, False for forbidden")
    path: str | None = None
    paths: list[str] = Field(default_factory=list)
    description: str = ""


class DependencyConstraint(BaseModel):
    """Dependency rule constraint."""

    model_config = ConfigDict(frozen=True)

    from_layer: str = Field(..., description="Source layer")
    to_layer: str = Field(..., description="Target layer")
    rule_type: str = Field(..., description="Type: layer_rule, max_depth, circular, forbidden_imports")
    max_depth: int | None = None
    description: str = ""


class Constraint(BaseModel):
    """A single constraint definition."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    category: ConstraintCategory
    level: ConstraintLevel
    pattern: str = ""
    service: str = ""
    target: str = ""
    from_layer: str = ""
    to_layer: str = ""
    rule_type: str = ""
    max_depth: int | None = None
    required: bool = True
    description: str = ""
    status: ConstraintStatus = ConstraintStatus.INACTIVE
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)

    @classmethod
    def from_dict(cls, data: dict) -> Constraint:
        """Create constraint from dictionary."""
        return cls(
            category=ConstraintCategory(data.get("category", "architecture")),
            level=ConstraintLevel(data.get("level", "hard")),
            pattern=data.get("pattern", ""),
            service=data.get("service", ""),
            target=data.get("target", ""),
            from_layer=data.get("from_layer", ""),
            to_layer=data.get("to_layer", ""),
            rule_type=data.get("rule_type", ""),
            max_depth=data.get("max_depth"),
            required=data.get("required", True),
            description=data.get("description", ""),
        )


class ConstraintViolation(BaseModel):
    """A violation of a constraint."""

    model_config = ConfigDict(frozen=True)

    constraint_id: UUID
    constraint_description: str
    level: ConstraintLevel
    category: ConstraintCategory
    affected_resource: str
    message: str
    suggestion: str = ""


class ConstraintValidationResult(BaseModel):
    """Result of validating constraints against current state."""

    is_valid: bool
    violations: list[ConstraintViolation] = Field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0

    @property
    def hard_violations(self) -> list[ConstraintViolation]:
        return [v for v in self.violations if v.level == ConstraintLevel.HARD]

    @property
    def soft_violations(self) -> list[ConstraintViolation]:
        return [v for v in self.violations if v.level == ConstraintLevel.SOFT]


class ConstraintConfig(BaseModel):
    """Configuration file structure for constraints."""

    architecture: list[dict] = Field(default_factory=list)
    technology: list[dict] = Field(default_factory=list)
    naming: list[dict] = Field(default_factory=list)
    patterns: list[dict] = Field(default_factory=list)
    dependencies: list[dict] = Field(default_factory=list)
    active_constraints: list[dict] = Field(default_factory=list)

    def to_constraints(self) -> list[Constraint]:
        """Convert config to constraint entities."""
        constraints = []

        for item in self.active_constraints:
            constraints.append(Constraint.from_dict(item))

        return constraints
