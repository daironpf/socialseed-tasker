"""Analysis engine for architectural integrity, root cause tracing, and causal traceability.

Evaluates architectural rules against issues and dependencies to detect
violations before they are persisted.
Provides root cause analysis and impact assessment capabilities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from socialseed_tasker.core.project_analysis.rules import (
    ArchitecturalRule,
    RuleType,
    ValidationResult,
    Violation,
)

if TYPE_CHECKING:
    from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface

from socialseed_tasker.core.task_management.entities import Issue

# --- Data Models for Root Cause Analysis ---


class RiskLevel(str, Enum):
    """Risk levels for impact analysis."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TestFailure(BaseModel):
    """Represents a failed test case."""

    model_config = ConfigDict(frozen=True)

    test_id: str
    test_name: str
    error_message: str
    stack_trace: str = ""
    component: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    labels: list[str] = Field(default_factory=list)


class CausalLink(BaseModel):
    """Represents a causal link between a failed test and a potential root cause issue."""

    issue: Issue  # Forward reference
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    graph_distance: int = Field(..., ge=0)
    temporal_distance: float  # hours


class ImpactAnalysis(BaseModel):
    """Represents the impact analysis of an issue."""

    issue_id: UUID
    directly_affected: list[Issue] = Field(default_factory=list)
    transitively_affected: list[Issue] = Field(default_factory=list)
    blocked_issues: list[Issue] = Field(default_factory=list)
    affected_components: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW


class ComponentImpactSummary(BaseModel):
    """Summary of an issue within component impact analysis."""

    id: str
    title: str
    status: str


class ComponentImpactAnalysis(BaseModel):
    """Represents the impact analysis of an entire component."""

    component_id: UUID
    component_name: str
    total_issues: int
    directly_affected_components: list[str] = Field(default_factory=list)
    transitively_affected_components: list[str] = Field(default_factory=list)
    total_blocked_issues: int = 0
    criticality_score: int = 0
    risk_level: RiskLevel = RiskLevel.LOW
    affected_issues_summary: list[ComponentImpactSummary] = Field(default_factory=list)


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

    def validate_dependency(self, issue_id: str, depends_on_id: str) -> ValidationResult:
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

    def _check_forbidden_technology(self, rule: ArchitecturalRule, issue: Issue) -> Violation | None:
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

    def _check_required_pattern(self, rule: ArchitecturalRule, issue: Issue) -> Violation | None:
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

    def _check_forbidden_dependency(self, rule: ArchitecturalRule, source: Issue, target: Issue) -> Violation | None:
        """Check if a dependency between two issues is forbidden."""
        source_comp = str(source.component_id)
        target_comp = str(target.component_id)

        if rule.source_pattern == source_comp and rule.target_pattern == target_comp:
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                message=(f"Dependency from component {source_comp[:8]} to {target_comp[:8]} is forbidden"),
                suggestion="Restructure the dependency to follow architectural boundaries",
            )
        return None

    def _check_max_depth(self, rule: ArchitecturalRule, issue_id: str) -> Violation | None:
        """Check if the dependency chain exceeds the maximum depth."""
        depth = self._get_dependency_depth(issue_id)
        if depth > rule.max_depth:
            return Violation(
                rule_id=rule.id,
                rule_name=rule.name,
                severity=rule.severity,
                message=(f"Dependency depth {depth} exceeds maximum allowed {rule.max_depth}"),
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


# --- Root Cause Analyzer ---


class RootCauseAnalyzer:
    """Analyzes test failures to find root causes and performs impact analysis.

    Intent: Provide capabilities to trace test failures to their root causes
    and analyze the impact of issues on the system.
    Business Value: Reduces debugging time by identifying likely culprits
    and helps teams understand the consequences of changes.
    """

    TECHNICAL_STOP_WORDS = {
        "fix",
        "bug",
        "issue",
        "update",
        "change",
        "add",
        "remove",
        "test",
        "tests",
        "testing",
        "error",
        "exception",
        "failed",
        "the",
        "a",
        "an",
        "is",
        "to",
        "in",
        "of",
        "and",
        "for",
        "on",
        "with",
    }

    def __init__(self, repository: TaskRepositoryInterface) -> None:
        self._repository = repository

    def find_root_cause(
        self,
        failed_test: TestFailure,
        closed_issues: list[Issue],
        min_confidence: float = 0.1,
    ) -> list[CausalLink]:
        """Find which recently closed issues are most likely responsible for a test failure.

        Uses graph proximity analysis to rank potential root causes:
        1. Direct dependency links (issue -> component that was modified)
        2. Shared component analysis (issue and test affect same component)
        3. Temporal proximity (recently closed issues are more likely culprits)
        4. Label/keyword matching between test failure and issue description
        """
        causal_links: list[CausalLink] = []

        for issue in closed_issues:
            reasons: list[str] = []
            score = 0.0

            component_match = str(issue.component_id) == failed_test.component
            if component_match:
                score += 0.3
                reasons.append(f"Same component: {failed_test.component}")

            if issue.closed_at:
                hours_ago = (datetime.now(timezone.utc) - issue.closed_at).total_seconds() / 3600
                if hours_ago < 24:
                    score += 0.3
                    reasons.append(f"Closed recently ({hours_ago:.1f}h ago)")
                elif hours_ago < 168:
                    score += 0.2
                    reasons.append(f"Closed within the week ({hours_ago:.1f}h ago)")

            test_labels = set(failed_test.labels)
            issue_labels = set(issue.labels)
            if test_labels & issue_labels:
                score += 0.2
                reasons.append(f"Shared labels: {test_labels & issue_labels}")

            test_text = f"{failed_test.test_name} {failed_test.error_message}".lower()
            issue_text = f"{issue.title} {issue.description}".lower()
            common_words = set(test_text.split()) & set(issue_text.split())
            meaningful_words = common_words - self.TECHNICAL_STOP_WORDS
            technical_matches = common_words & self.TECHNICAL_STOP_WORDS
            semantic_bonus = max(0, 0.2 - (len(technical_matches) * 0.02))
            if len(meaningful_words) > 2:
                score += semantic_bonus
                reasons.append(f"Semantic overlap: {len(meaningful_words)} meaningful words")

            graph_distance = self._calculate_graph_distance(issue, failed_test)
            if graph_distance == 0:
                score += 0.2
                reasons.append("Same component")
            elif graph_distance <= 1:
                score += 0.2
                reasons.append(f"Direct graph proximity (distance={graph_distance})")
            elif graph_distance <= 3:
                score += 0.1
                reasons.append(f"Close graph proximity (distance={graph_distance})")

            if score >= min_confidence:
                causal_links.append(
                    CausalLink(
                        issue=issue,
                        confidence=min(score, 1.0),
                        reasons=reasons,
                        graph_distance=graph_distance,
                        temporal_distance=hours_ago if issue.closed_at else -1.0,
                    )
                )

        causal_links.sort(key=lambda link: link.confidence, reverse=True)
        return causal_links

    def _calculate_graph_distance(self, issue: Issue, failed_test: TestFailure, max_distance: int = 3) -> int:
        """Calculate the shortest graph distance between an issue and a test's component.

        Traverses both directions (dependents and dependencies) up to max_distance.
        """
        if str(issue.component_id) == failed_test.component:
            return 0

        visited: set[str] = {str(issue.id)}
        queue: list[tuple[str, int]] = [(str(issue.id), 0)]

        while queue:
            current_id, distance = queue.pop(0)
            if distance >= max_distance:
                continue
            current_issue = self._repository.get_issue(current_id)
            if current_issue is None:
                continue

            dependents = self._repository.get_dependents(current_id)
            dependencies = self._repository.get_dependencies(current_id)
            all_connected = dependents + dependencies

            for connected in all_connected:
                conn_id = str(connected.id)
                if conn_id not in visited:
                    visited.add(conn_id)
                    if str(connected.component_id) == failed_test.component:
                        return distance + 1
                    queue.append((conn_id, distance + 1))

        return 999

    def analyze_impact(self, issue_id: str) -> ImpactAnalysis:
        """Analyze what other issues and components would be affected if this issue changes.

        Traverses the graph to find:
        - All issues that DEPENDS_ON this issue (direct dependents)
        - Transitive dependents (issues affected by affected issues)
        - Blocked issues (dependents with all dependencies satisfied except this one)
        - Affected components (unique components of affected issues)
        - Risk level based on impact scope
        """
        issue = self._repository.get_issue(issue_id)
        if issue is None:
            return ImpactAnalysis(
                issue_id=UUID(issue_id),
                directly_affected=[],
                transitively_affected=[],
                blocked_issues=[],
                affected_components=[],
                risk_level=RiskLevel.LOW,
            )

        directly_affected = self._repository.get_dependents(issue_id)
        directly_affected_ids = {str(d.id) for d in directly_affected}

        transitive_affected: list[Issue] = []
        transitive_visited: set[str] = set(directly_affected_ids)
        queue: list[str] = list(directly_affected_ids)

        while queue:
            current_id = queue.pop(0)
            dependents = self._repository.get_dependents(current_id)
            for dep in dependents:
                dep_id = str(dep.id)
                if dep_id not in transitive_visited:
                    transitive_visited.add(dep_id)
                    transitive_affected.append(dep)
                    queue.append(dep_id)

        blocked_issues = self._find_blocked_by(issue_id, directly_affected)

        affected_components = self._collect_affected_components(
            directly_affected + transitive_affected + blocked_issues
        )

        risk_level = self._calculate_risk_level(len(directly_affected), len(transitive_affected), len(blocked_issues))

        return ImpactAnalysis(
            issue_id=issue.id,
            directly_affected=directly_affected,
            transitively_affected=transitive_affected,
            blocked_issues=blocked_issues,
            affected_components=affected_components,
            risk_level=risk_level,
        )

    def _find_blocked_by(self, source_id: str, dependents: list[Issue]) -> list[Issue]:
        """Find issues that are blocked because they depend on the source issue."""
        blocked: list[Issue] = []
        for dep in dependents:
            dep_dependencies = self._repository.get_dependencies(str(dep.id))
            open_deps = [d for d in dep_dependencies if d.status.value != "CLOSED" and str(d.id) != source_id]
            if not open_deps:
                blocked.append(dep)
        return blocked

    def _collect_affected_components(self, issues: list[Issue]) -> list[str]:
        """Collect unique component IDs from a list of issues."""
        components: set[str] = set()
        for issue in issues:
            components.add(str(issue.component_id))
        return sorted(components)

    def _calculate_risk_level(self, direct_count: int, transitive_count: int, blocked_count: int) -> RiskLevel:
        """Calculate risk level based on the scope of impact."""
        total_impact = direct_count + (transitive_count * 0.5) + (blocked_count * 2)

        if total_impact >= 10 or blocked_count >= 5:
            return RiskLevel.CRITICAL
        if total_impact >= 5 or blocked_count >= 3:
            return RiskLevel.HIGH
        if total_impact >= 2 or blocked_count >= 1:
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def analyze_component_impact(self, component_id: str) -> ComponentImpactAnalysis:
        """Analyze the impact of an entire component.

        Traverses all issues in the component and computes:
        - Combined impact across all issues
        - Directly affected components
        - Transitively affected components
        - Total blocked issues
        - Criticality score (how many other components depend on this one)
        - Overall risk level
        """
        component = self._repository.get_component(component_id)
        if component is None:
            return ComponentImpactAnalysis(
                component_id=UUID(component_id),
                component_name="Unknown",
                total_issues=0,
                risk_level=RiskLevel.LOW,
            )

        issues = self._repository.list_issues(component_id=component_id)
        total_issues = len(issues)

        all_directly_affected_ids: set[str] = set()
        all_transitively_affected_ids: set[str] = set()
        all_blocked_issue_ids: set[str] = set()

        for issue in issues:
            impact = self.analyze_impact(str(issue.id))
            for da in impact.directly_affected:
                all_directly_affected_ids.add(str(da.id))
            for ta in impact.transitively_affected:
                all_transitively_affected_ids.add(str(ta.id))
            for bi in impact.blocked_issues:
                all_blocked_issue_ids.add(str(bi.id))

        directly_affected_components: set[str] = set()
        transitively_affected_components: set[str] = set()

        for issue_id in all_directly_affected_ids:
            issue = self._repository.get_issue(issue_id)
            if issue:
                directly_affected_components.add(str(issue.component_id))

        for issue_id in all_transitively_affected_ids:
            issue = self._repository.get_issue(issue_id)
            if issue:
                transitively_affected_components.add(str(issue.component_id))

        directly_affected_components.discard(component_id)
        transitively_affected_components.discard(component_id)

        all_affected_components = directly_affected_components | transitively_affected_components

        criticality_score = len(all_affected_components)

        direct_count = len(all_directly_affected_ids)
        transitive_count = len(all_transitively_affected_ids)
        blocked_count = len(all_blocked_issue_ids)
        risk_level = self._calculate_risk_level(direct_count, transitive_count, blocked_count)

        affected_summary = []
        for issue in issues:
            affected_summary.append(
                ComponentImpactSummary(
                    id=str(issue.id),
                    title=issue.title,
                    status=issue.status.value,
                )
            )

        return ComponentImpactAnalysis(
            component_id=component.id,
            component_name=component.name,
            total_issues=total_issues,
            directly_affected_components=sorted(directly_affected_components),
            transitively_affected_components=sorted(transitively_affected_components),
            total_blocked_issues=len(all_blocked_issue_ids),
            criticality_score=criticality_score,
            risk_level=risk_level,
            affected_issues_summary=affected_summary,
        )
