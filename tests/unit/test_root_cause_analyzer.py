"""Tests for the root cause analyzer and impact analysis functionality."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from socialseed_tasker.core.project_analysis.analyzer import (
    CausalLink,
    ImpactAnalysis,
    RiskLevel,
    RootCauseAnalyzer,
    TestFailure,
)
from socialseed_tasker.core.task_management.entities import (
    Issue,
    IssuePriority,
    IssueStatus,
)

# --- Test helpers ---


def _make_issue(
    component_id: UUID,
    status: IssueStatus = IssueStatus.CLOSED,
    closed_at: datetime | None = None,
    labels: list[str] | None = None,
    title: str = "Test issue",
    description: str = "Test description",
) -> Issue:
    return Issue(
        component_id=component_id,
        title=title,
        description=description,
        status=status,
        priority=IssuePriority.MEDIUM,
        closed_at=closed_at,
        labels=labels or [],
    )


class _MockRepo:
    """Minimal mock repository for root cause / impact tests."""

    def __init__(self) -> None:
        self._issues: dict[str, Issue] = {}
        self._dependents: dict[str, list[Issue]] = {}
        self._dependencies: dict[str, list[Issue]] = {}

    def add_issue(self, issue: Issue) -> None:
        self._issues[str(issue.id)] = issue

    def set_dependents(self, issue_id: str, dependents: list[Issue]) -> None:
        self._dependents[issue_id] = dependents

    def set_dependencies(self, issue_id: str, dependencies: list[Issue]) -> None:
        self._dependencies[issue_id] = dependencies

    def get_issue(self, issue_id: str) -> Issue | None:
        return self._issues.get(issue_id)

    def get_dependents(self, issue_id: str) -> list[Issue]:
        return self._dependents.get(issue_id, [])

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        return self._dependencies.get(issue_id, [])

    def list_issues(
        self,
        component_id: str | None = None,
        status: IssueStatus | None = None,
        project: str | None = None,
    ) -> list[Issue]:
        result = list(self._issues.values())
        if status:
            result = [i for i in result if i.status == status]
        if component_id:
            result = [i for i in result if str(i.component_id) == component_id]
        return result


# --- TestFailure ---


def test_test_failure_creation() -> None:
    test_failure = TestFailure(
        test_id="test_123",
        test_name="test_example",
        error_message="AssertionError: Expected 5, got 3",
        component="auth-service",
        labels=["unit-test", "auth"],
    )
    assert test_failure.test_id == "test_123"
    assert test_failure.component == "auth-service"
    assert "unit-test" in test_failure.labels


# --- Root Cause Analysis ---


def test_find_root_cause_no_closed_issues() -> None:
    repo = _MockRepo()
    analyzer = RootCauseAnalyzer(repo)
    test_failure = TestFailure(
        test_id="t1",
        test_name="test_api",
        error_message="Connection refused",
        component="api",
        labels=["integration"],
    )
    result = analyzer.find_root_cause(test_failure, [])
    assert result == []


def test_find_root_cause_component_match() -> None:
    repo = _MockRepo()
    comp_id = uuid4()
    issue = _make_issue(
        component_id=comp_id,
        closed_at=datetime.now(timezone.utc) - timedelta(hours=2),
        labels=["api", "backend"],
        title="Refactor API gateway",
        description="Updated the API gateway configuration",
    )
    repo.add_issue(issue)

    test_failure = TestFailure(
        test_id="t1",
        test_name="test_api_gateway",
        error_message="Connection refused after gateway update",
        component=str(comp_id),
        labels=["api", "backend"],
    )

    analyzer = RootCauseAnalyzer(repo)
    result = analyzer.find_root_cause(test_failure, [issue])

    assert len(result) == 1
    link = result[0]
    assert isinstance(link, CausalLink)
    assert link.issue.id == issue.id
    assert link.confidence > 0.5
    assert any("Same component" in r for r in link.reasons)
    assert any("Shared labels" in r for r in link.reasons)


def test_find_root_cause_temporal_recency() -> None:
    repo = _MockRepo()
    comp_id = uuid4()
    recent_issue = _make_issue(
        component_id=comp_id,
        closed_at=datetime.now(timezone.utc) - timedelta(hours=1),
        title="Recent change",
        description="Changed something",
    )
    old_issue = _make_issue(
        component_id=comp_id,
        closed_at=datetime.now(timezone.utc) - timedelta(days=30),
        title="Old change",
        description="Old change description",
    )
    repo.add_issue(recent_issue)
    repo.add_issue(old_issue)

    test_failure = TestFailure(
        test_id="t1",
        test_name="test_something",
        error_message="Something broke",
        component=str(comp_id),
    )

    analyzer = RootCauseAnalyzer(repo)
    result = analyzer.find_root_cause(test_failure, [recent_issue, old_issue])

    assert len(result) == 2
    assert result[0].confidence >= result[1].confidence


def test_find_root_cause_no_match() -> None:
    repo = _MockRepo()
    comp_id = uuid4()
    issue = _make_issue(
        component_id=comp_id,
        closed_at=datetime.now(timezone.utc) - timedelta(days=10),
        title="Unrelated issue",
        description="This has nothing to do with the test",
    )
    repo.add_issue(issue)

    test_failure = TestFailure(
        test_id="t1",
        test_name="test_database",
        error_message="Database timeout",
        component="different-component",
        labels=["database"],
    )

    analyzer = RootCauseAnalyzer(repo)
    result = analyzer.find_root_cause(test_failure, [issue])

    assert len(result) == 0


# --- Impact Analysis ---


def test_analyze_impact_no_data() -> None:
    repo = _MockRepo()
    analyzer = RootCauseAnalyzer(repo)
    issue_id = uuid4()

    result = analyzer.analyze_impact(str(issue_id))

    assert isinstance(result, ImpactAnalysis)
    assert result.issue_id == issue_id
    assert result.directly_affected == []
    assert result.transitively_affected == []
    assert result.blocked_issues == []
    assert result.affected_components == []
    assert result.risk_level == RiskLevel.LOW


def test_analyze_impact_with_dependents() -> None:
    repo = _MockRepo()
    comp_a = uuid4()
    comp_b = uuid4()

    source_issue = _make_issue(component_id=comp_a, status=IssueStatus.OPEN, title="Source")
    dep1 = _make_issue(component_id=comp_b, status=IssueStatus.OPEN, title="Dependent 1")
    dep2 = _make_issue(component_id=comp_b, status=IssueStatus.OPEN, title="Dependent 2")

    repo.add_issue(source_issue)
    repo.add_issue(dep1)
    repo.add_issue(dep2)
    repo.set_dependents(str(source_issue.id), [dep1, dep2])

    analyzer = RootCauseAnalyzer(repo)
    result = analyzer.analyze_impact(str(source_issue.id))

    assert len(result.directly_affected) == 2
    assert result.risk_level in (RiskLevel.MEDIUM, RiskLevel.HIGH)
    assert str(comp_b) in result.affected_components


def test_analyze_impact_transitive() -> None:
    repo = _MockRepo()
    comp_a = uuid4()
    comp_b = uuid4()
    comp_c = uuid4()

    source = _make_issue(component_id=comp_a, title="Source")
    direct = _make_issue(component_id=comp_b, title="Direct dependent")
    transitive = _make_issue(component_id=comp_c, title="Transitive dependent")

    repo.add_issue(source)
    repo.add_issue(direct)
    repo.add_issue(transitive)
    repo.set_dependents(str(source.id), [direct])
    repo.set_dependents(str(direct.id), [transitive])

    analyzer = RootCauseAnalyzer(repo)
    result = analyzer.analyze_impact(str(source.id))

    assert len(result.directly_affected) == 1
    assert len(result.transitively_affected) == 1
    assert result.transitively_affected[0].title == "Transitive dependent"


def test_analyze_impact_risk_critical() -> None:
    repo = _MockRepo()
    comp_a = uuid4()
    comp_b = uuid4()

    source = _make_issue(component_id=comp_a, title="Source")
    blocked_issues = [_make_issue(component_id=comp_b, title=f"Blocked {i}") for i in range(6)]

    repo.add_issue(source)
    for b in blocked_issues:
        repo.add_issue(b)
    repo.set_dependents(str(source.id), blocked_issues)
    for b in blocked_issues:
        repo.set_dependencies(str(b.id), [])

    analyzer = RootCauseAnalyzer(repo)
    result = analyzer.analyze_impact(str(source.id))

    assert result.risk_level == RiskLevel.CRITICAL


def test_risk_level_enum() -> None:
    assert RiskLevel.LOW == "LOW"
    assert RiskLevel.MEDIUM == "MEDIUM"
    assert RiskLevel.HIGH == "HIGH"
    assert RiskLevel.CRITICAL == "CRITICAL"
