"""Analysis engine for architectural integrity and root cause tracing.

Evaluates architectural rules against issues and dependencies to detect
violations before they are persisted.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from socialseed_tasker.core.project_analysis.rules import (
    ArchitecturalRule,
    RuleType,
    Severity,
    ValidationResult,
    Violation,
)

if TYPE_CHECKING:
    from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface
    from socialseed_tasker.core.task_management.entities import Issue


class ArchitecturalAnalyzer:
    """Evaluates architectural rules against issues and dependencies.

    Intent: Provide a reusable engine that checks actions against
    user-defined architectural rules.
    Business Value: Prevents architectural violations by catching them
    at the point of creation rather than during code review.
    """

    def __init__(self, repository: TaskRepositoryInterface) -> None:
        self._repository = repository
        self._rules: list[ArchitecturalRule] = []

    # -- Rule management -----------------------------------------------------

    def add_rule(self, rule: ArchitecturalRule) -> None:
        """Register a new architectural rule."""
        self._rules.append(rule)

    def remove_rule(self, rule_id: str) -> None:
        """Remove a rule by ID."""
        self._rules = [r for r in self._rules if str(r.id) != rule_id]

    def list_rules(self) -> list[ArchitecturalRule]:
        """Return all active rules."""
        return [r for r in self._rules if r.is_active]

    # -- Validation ----------------------------------------------------------

    def validate_issue_creation(self, issue: Issue) -> ValidationResult:
        """Check if creating this issue violates any architectural rules.

        Evaluates FORBIDDEN_TECHNOLOGY and REQUIRED_PATTERN rules
        against the issue's labels, description, and component.
        """
        violations: list[Violation] = []
        active_rules = self.list_rules()

        for rule in active_rules:
            if rule.rule_type == RuleType.FORBIDDEN_TECHNOLOGY:
                v = self._check_forbidden_technology(rule, issue)
                if v:
                    violations.append(v)
            elif rule.rule_type == RuleType.REQUIRED_PATTERN:
                v = self._check_required_pattern(rule, issue)
                if v:
                    violations.append(v)

        return ValidationResult(violations=violations)

    def validate_dependency(
        self, issue_id: str, depends_on_id: str
    ) -> ValidationResult:
        """Check if adding a dependency violates any architectural rules.

        Evaluates FORBIDDEN_DEPENDENCY rules between the two issues'
        components.
        """
        violations: list[Violation] = []
        active_rules = self.list_rules()

        issue = self._repository.get_issue(issue_id)
        target = self._repository.get_issue(depends_on_id)

        if issue is None or target is None:
            return ValidationResult(violations=violations)

        for rule in active_rules:
            if rule.rule_type == RuleType.FORBIDDEN_DEPENDENCY:
                v = self._check_forbidden_dependency(rule, issue, target)
                if v:
                    violations.append(v)
            elif rule.rule_type == RuleType.MAX_DEPENDENCY_DEPTH:
                v = self._check_max_depth(rule, issue_id)
                if v:
                    violations.append(v)

        return ValidationResult(violations=violations)

    # -- Rule evaluators -----------------------------------------------------

    def _check_forbidden_technology(
        self, rule: ArchitecturalRule, issue: Issue
    ) -> Violation | None:
        """Check if the issue uses a forbidden technology."""
        forbidden = rule.source_pattern.lower()
        text = f"{issue.description} {' '.join(issue.labels)}".lower()
        if forbidden in text:
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                message=f"Issue uses forbidden technology '{forbidden}'",
                suggestion=f"Remove references to '{forbidden}' from the issue",
            )
        return None

    def _check_required_pattern(
        self, rule: ArchitecturalRule, issue: Issue
    ) -> Violation | None:
        """Check if the issue follows a required pattern."""
        required_label = rule.source_pattern
        if required_label and required_label not in issue.labels:
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                message=f"Issue is missing required label '{required_label}'",
                suggestion=f"Add the '{required_label}' label to this issue",
            )
        return None

    def _check_forbidden_dependency(
        self, rule: ArchitecturalRule, source: Issue, target: Issue
    ) -> Violation | None:
        """Check if a dependency between two issues is forbidden."""
        source_comp = str(source.component_id)
        target_comp = str(target.component_id)

        if rule.source_pattern == source_comp and rule.target_pattern == target_comp:
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                message=(
                    f"Dependency from component {source_comp[:8]} to "
                    f"{target_comp[:8]} is forbidden"
                ),
                suggestion="Restructure the dependency to follow architectural boundaries",
            )
        return None

    def _check_max_depth(
        self, rule: ArchitecturalRule, issue_id: str
    ) -> Violation | None:
        """Check if the dependency chain exceeds the maximum depth."""
        depth = self._get_dependency_depth(issue_id)
        if depth > rule.max_depth:
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                message=(
                    f"Dependency depth {depth} exceeds maximum allowed {rule.max_depth}"
                ),
                suggestion="Reduce the dependency chain length",
            )
        return None

    def _get_dependency_depth(self, issue_id: str, visited: set[str] | None = None) -> int:
        """Calculate the maximum depth of the dependency chain."""
        if visited is None:
            visited = set()

        if issue_id in visited:
            return 0
        visited.add(issue_id)

        deps = self._repository.get_dependencies(issue_id)
        if not deps:
            return 0

        return 1 + max(self._get_dependency_depth(str(d.id), visited) for d in deps)
