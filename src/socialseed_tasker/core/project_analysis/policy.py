"""Policy definitions for graph-based architectural governance.

Defines Policy and PolicyRule entities that encode architectural constraints
as machine-checkable rules for enforcement at write time.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


def _now() -> datetime:
    return datetime.now(timezone.utc)


class PolicyRuleType(str, Enum):
    """Types of policy rules."""

    FORBIDDEN_PATH = "forbidden_path"
    REQUIRED_DEPENDENCY = "required_dependency"
    MAX_DEPTH = "max_depth"
    FORBIDDEN_LABEL_DEPENDENCY = "forbidden_label_dependency"


class PolicyRule(BaseModel):
    """A single rule within a policy."""

    model_config = ConfigDict(frozen=True)

    rule_type: PolicyRuleType
    from_pattern: str = Field(
        "",
        description="Pattern to match source component/label (e.g., 'component.type:frontend')",
    )
    to_pattern: str = Field(
        "",
        description="Pattern to match target component/label (e.g., 'component.type:database')",
    )
    max_depth: int = Field(
        default=5,
        description="Maximum depth for max_depth rules",
        ge=1,
    )
    description: str = ""


class Policy(BaseModel):
    """A policy containing multiple rules for architectural governance.

    Intent: Encode architectural boundaries as machine-checkable policies
    so the system can enforce them at write time.
    Business Value: Prevents architectural drift by blocking actions that
    violate defined architectural constraints.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    rules: list[PolicyRule] = Field(default_factory=list)
    is_active: bool = True
    created_at: datetime = Field(default_factory=_now)
    updated_at: datetime = Field(default_factory=_now)


class PolicyViolation(BaseModel):
    """A violation of a policy rule."""

    policy_id: UUID
    policy_name: str
    rule_type: PolicyRuleType
    message: str
    suggestion: str = ""


class PolicyValidationResult(BaseModel):
    """Result of validating an action against policies."""

    is_valid: bool
    violations: list[PolicyViolation] = Field(default_factory=list)

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0


class PolicyEngine:
    """Engine for evaluating policies against graph actions.

    Intent: Provide a centralized mechanism for checking if proposed
    actions violate any defined architectural policies.
    Business Value: Enables proactive enforcement of architectural
    boundaries before violations are persisted.
    """

    def __init__(self, policies: list[Policy] | None = None) -> None:
        self._policies: list[Policy] = policies or []

    def add_policy(self, policy: Policy) -> None:
        """Add a policy to the engine."""
        self._policies.append(policy)

    def remove_policy(self, policy_id: UUID) -> None:
        """Remove a policy by ID."""
        self._policies = [p for p in self._policies if p.id != policy_id]

    def list_policies(self) -> list[Policy]:
        """List all active policies."""
        return [p for p in self._policies if p.is_active]

    def get_policy(self, policy_id: UUID) -> Policy | None:
        """Get a policy by ID."""
        for p in self._policies:
            if p.id == policy_id:
                return p
        return None

    def validate_dependency(
        self,
        from_component_name: str,
        from_component_type: str,
        from_labels: list[str],
        to_component_name: str,
        to_component_type: str,
        to_labels: list[str],
    ) -> PolicyValidationResult:
        """Validate adding a dependency against all policies."""
        violations: list[PolicyViolation] = []

        for policy in self.list_policies():
            for rule in policy.rules:
                violation = self._check_rule(
                    rule,
                    from_component_name,
                    from_component_type,
                    from_labels,
                    to_component_name,
                    to_component_type,
                    to_labels,
                    policy,
                )
                if violation:
                    violations.append(violation)

        return PolicyValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
        )

    def _check_rule(
        self,
        rule: PolicyRule,
        from_comp_name: str,
        from_comp_type: str,
        from_labels: list[str],
        to_comp_name: str,
        to_comp_type: str,
        to_labels: list[str],
        policy: Policy | None = None,
    ) -> PolicyViolation | None:
        """Check a single rule against the given components."""
        if rule.rule_type == PolicyRuleType.FORBIDDEN_PATH:
            return self._check_forbidden_path(
                rule, from_comp_name, from_comp_type, from_labels, to_comp_name, to_comp_type, to_labels, policy
            )
        elif rule.rule_type == PolicyRuleType.FORBIDDEN_LABEL_DEPENDENCY:
            return self._check_forbidden_label(rule, from_labels, to_labels, policy)
        return None

    def _check_forbidden_path(
        self,
        rule: PolicyRule,
        from_comp_name: str,
        from_comp_type: str,
        from_labels: list[str],
        to_comp_name: str,
        to_comp_type: str,
        to_labels: list[str],
        policy: Policy | None = None,
    ) -> PolicyViolation | None:
        """Check if the dependency creates a forbidden path."""
        from_matches = self._pattern_matches(rule.from_pattern, from_comp_name, from_comp_type, from_labels)
        to_matches = self._pattern_matches(rule.to_pattern, to_comp_name, to_comp_type, to_labels)

        if from_matches and to_matches:
            return PolicyViolation(
                policy_id=policy.id if policy else uuid4(),
                policy_name=policy.name if policy else "",
                rule_type=rule.rule_type,
                message=f"Forbidden path: {rule.from_pattern} cannot depend on {rule.to_pattern}",
                suggestion=f"Remove the dependency or restructure to avoid {rule.to_pattern}",
            )
        return None

    def _check_forbidden_label(
        self,
        rule: PolicyRule,
        from_labels: list[str],
        to_labels: list[str],
        policy: Policy | None = None,
    ) -> PolicyViolation | None:
        """Check if labels create a forbidden dependency."""
        from_matches = any(label in from_labels for label in rule.from_pattern.split(","))
        to_matches = any(label in to_labels for label in rule.to_pattern.split(","))

        if from_matches and to_matches:
            return PolicyViolation(
                policy_id=policy.id if policy else uuid4(),
                policy_name=policy.name if policy else "",
                rule_type=rule.rule_type,
                message=(
                    f"Forbidden label dependency: labels matching "
                    f"'{rule.from_pattern}' cannot depend on '{rule.to_pattern}'"
                ),
                suggestion="Remove the label dependency or use a different approach",
            )
        return None

    def _pattern_matches(
        self,
        pattern: str,
        component_name: str,
        component_type: str,
        labels: list[str],
    ) -> bool:
        """Check if a pattern matches the given component."""
        if not pattern:
            return False

        if pattern.startswith("component.type:"):
            expected_type = pattern.split(":")[1]
            return component_type == expected_type

        if pattern.startswith("component.name:"):
            expected_name = pattern.split(":")[1]
            return component_name == expected_name

        if pattern.startswith("label:"):
            expected_label = pattern.split(":")[1]
            return expected_label in labels

        return pattern in labels or pattern == component_name
