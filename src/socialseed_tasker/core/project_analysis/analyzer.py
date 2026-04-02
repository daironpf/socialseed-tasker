"""Analysis engine for architectural integrity, root cause tracing, and causal traceability.

Evaluates architectural rules against issues and dependencies to detect
violations before they are persisted.
Provides root cause analysis and impact assessment capabilities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

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
    
    issue: 'Issue'  # Forward reference
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasons: list[str] = Field(default_factory=list)
    graph_distance: int = Field(..., ge=0)
    temporal_distance: float  # hours


class ImpactAnalysis(BaseModel):
    """Represents the impact analysis of an issue."""
    
    issue_id: UUID
    directly_affected: list['Issue'] = Field(default_factory=list)
    transitively_affected: list['Issue'] = Field(default_factory=list)
    blocked_issues: list['Issue'] = Field(default_factory=list)
    affected_components: list[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW


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


# --- Root Cause Analyzer ---


class RootCauseAnalyzer:
    """Analyzes test failures to find root causes and performs impact analysis.
    
    Intent: Provide capabilities to trace test failures to their root causes
    and analyze the impact of issues on the system.
    Business Value: Reduces debugging time by identifying likely culprits
    and helps teams understand the consequences of changes.
    """
    
    def __init__(self, repository: TaskRepositoryInterface) -> None:
        self._repository = repository
    
    def find_root_cause(self, failed_test_id: str, closed_issues: list[Issue]) -> list:
        """
        Find which recently closed issues are most likely responsible for a test failure.
        
        Uses graph proximity analysis to rank potential root causes:
        1. Direct dependency links (issue -> component that was modified)
        2. Shared component analysis (issue and test affect same component)
        3. Temporal proximity (recently closed issues are more likely culprits)
        4. Label/keyword matching between test failure and issue description
        """
        # Placeholder implementation - returns empty list
        # In a full implementation, this would:
        # 1. Get the failed test details from test failure data
        # 2. Analyze closed issues for potential causal links
        # 3. Score each issue based on proximity factors
        # 4. Return ranked list of CausalLink objects
        return []
    
    def analyze_impact(self, issue_id: str) -> dict:
        """
        Analyze what other issues and components would be affected if this issue changes.
        
        Traverses the graph to find:
        - All issues that DEPENDS_ON this issue
        - All issues that this issue BLOCKS
        - All issues that this issue AFFECTS
        - Transitive impact (issues affected by affected issues)
        """
        # Placeholder implementation - returns basic structure
        # In a full implementation, this would:
        # 1. Get the issue from the repository
        # 2. Find all dependents (directly affected)
        # 3. Find transitive dependencies
        # 4. Find blocked issues
        # 5. Calculate risk level based on impact scope
        return {
            "issue_id": issue_id,
            "directly_affected": [],
            "transitively_affected": [],
            "blocked_issues": [],
            "affected_components": [],
            "risk_level": "LOW"
        }
    
    def get_proximity_score(self, issue: Issue, failed_test: dict) -> float:
        """
        Calculate a proximity score indicating how likely this issue is the root cause.
        
        Scoring factors:
        - Direct graph distance (shortest path in dependency graph)
        - Component overlap (same component = higher score)
        - Temporal recency (more recently closed = higher score)
        - Semantic similarity (keyword/label overlap)
        """
        # Simplified implementation
        score = 0.0
        
        # Component overlap
        if issue and str(issue.component_id) == failed_test.get("component", ""):
            score += 0.3
        
        # Temporal recency
        if issue and issue.closed_at:
            hours_ago = (datetime.now(timezone.utc) - issue.closed_at).total_seconds() / 3600
            if hours_ago < 24:  # Less than a day
                score += 0.3
            elif hours_ago < 168:  # Less than a week
                score += 0.2
        
        # Label/keyword matching (simplified)
        if issue:
            test_labels = set(failed_test.get("labels", []))
            issue_labels = set(issue.labels)
            if test_labels & issue_labels:  # Intersection
                score += 0.2
        
        # Simple semantic similarity
        if issue:
            test_text = f"{failed_test.get('test_name', '')} {failed_test.get('error_message', '')}".lower()
            issue_text = f"{issue.title} {issue.description}".lower()
            common_words = set(test_text.split()) & set(issue_text.split())
            if len(common_words) > 2:
                score += 0.2
        
        return min(score, 1.0)
