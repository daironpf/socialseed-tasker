"""Tests for architectural rules and analyzer."""

from uuid import uuid4

import pytest

from socialseed_tasker.core.project_analysis.analyzer import ArchitecturalAnalyzer
from socialseed_tasker.core.project_analysis.rules import (
    ArchitecturalRule,
    RuleType,
    Severity,
    ValidationResult,
    Violation,
)
from socialseed_tasker.core.task_management.entities import Component, Issue


class FakeRepo:
    """Minimal repository for testing the analyzer."""

    def __init__(self) -> None:
        self._issues: dict[str, Issue] = {}
        self._components: dict[str, Component] = {}
        self._deps: dict[str, set[str]] = {}

    def create_component(self, c: Component) -> None:
        self._components[str(c.id)] = c

    def create_issue(self, i: Issue) -> None:
        self._issues[str(i.id)] = i
        self._deps[str(i.id)] = set()

    def get_issue(self, issue_id: str) -> Issue | None:
        return self._issues.get(issue_id)

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        dep_ids = self._deps.get(issue_id, set())
        return [self._issues[d] for d in dep_ids if d in self._issues]

    def add_dependency(self, issue_id: str, depends_on_id: str) -> None:
        self._deps.setdefault(issue_id, set()).add(depends_on_id)

    def list_issues(self, **_):
        return list(self._issues.values())

    def get_component(self, cid):
        return self._components.get(cid)

    def list_components(self, **_):
        return list(self._components.values())


class TestArchitecturalRule:
    def test_create_rule(self):
        rule = ArchitecturalRule(
            name="No SQL in graph module",
            rule_type=RuleType.FORBIDDEN_TECHNOLOGY,
            source_pattern="sql",
        )
        assert rule.is_active is True
        assert rule.severity == Severity.ERROR

    def test_rule_is_frozen(self):
        rule = ArchitecturalRule(
            name="Test",
            rule_type=RuleType.FORBIDDEN_TECHNOLOGY,
        )
        with pytest.raises(Exception):
            rule.name = "Changed"


class TestValidationResult:
    def test_empty_is_valid(self):
        result = ValidationResult()
        assert result.is_valid is True
        assert result.has_errors is False
        assert result.has_warnings is False

    def test_with_error(self):
        result = ValidationResult(
            violations=[
                Violation(
                    rule_id=uuid4(),
                    rule_name="Test",
                    severity=Severity.ERROR,
                    message="Error",
                )
            ]
        )
        assert result.is_valid is False
        assert result.has_errors is True
        assert result.has_warnings is False

    def test_with_warning(self):
        result = ValidationResult(
            violations=[
                Violation(
                    rule_id=uuid4(),
                    rule_name="Test",
                    severity=Severity.WARNING,
                    message="Warning",
                )
            ]
        )
        assert result.is_valid is False
        assert result.has_errors is False
        assert result.has_warnings is True


class TestArchitecturalAnalyzer:
    @pytest.fixture()
    def repo(self):
        return FakeRepo()

    @pytest.fixture()
    def analyzer(self, repo):
        return ArchitecturalAnalyzer(repo)

    def test_rule_management(self, analyzer):
        rule = ArchitecturalRule(
            name="Test rule",
            rule_type=RuleType.FORBIDDEN_TECHNOLOGY,
            source_pattern="sql",
        )
        analyzer.add_rule(rule)
        assert len(analyzer.list_rules()) == 1

        analyzer.remove_rule(str(rule.id))
        assert len(analyzer.list_rules()) == 0

    def test_forbidden_technology_violation(self, analyzer):
        rule = ArchitecturalRule(
            name="No SQL",
            rule_type=RuleType.FORBIDDEN_TECHNOLOGY,
            source_pattern="sql",
        )
        analyzer.add_rule(rule)

        issue = Issue(title="Test", component_id=uuid4(), description="Uses SQL database")
        result = analyzer.validate_issue_creation(issue)
        assert result.has_errors is True
        assert "sql" in result.violations[0].message.lower()

    def test_forbidden_technology_no_violation(self, analyzer):
        rule = ArchitecturalRule(
            name="No SQL",
            rule_type=RuleType.FORBIDDEN_TECHNOLOGY,
            source_pattern="sql",
        )
        analyzer.add_rule(rule)

        issue = Issue(title="Test", component_id=uuid4(), description="Uses Neo4j graph")
        result = analyzer.validate_issue_creation(issue)
        assert result.is_valid is True

    def test_required_pattern_violation(self, analyzer):
        rule = ArchitecturalRule(
            name="Must have test label",
            rule_type=RuleType.REQUIRED_PATTERN,
            source_pattern="test",
        )
        analyzer.add_rule(rule)

        issue = Issue(title="Test", component_id=uuid4(), labels=["feature"])
        result = analyzer.validate_issue_creation(issue)
        assert result.has_errors is True

    def test_required_pattern_no_violation(self, analyzer):
        rule = ArchitecturalRule(
            name="Must have test label",
            rule_type=RuleType.REQUIRED_PATTERN,
            source_pattern="test",
        )
        analyzer.add_rule(rule)

        issue = Issue(title="Test", component_id=uuid4(), labels=["test", "feature"])
        result = analyzer.validate_issue_creation(issue)
        assert result.is_valid is True

    def test_forbidden_dependency_violation(self, analyzer, repo):
        comp_ui = Component(name="UI", project="test")
        comp_db = Component(name="DB", project="test")
        repo.create_component(comp_ui)
        repo.create_component(comp_db)

        ui_issue = Issue(title="UI", component_id=comp_ui.id)
        db_issue = Issue(title="DB", component_id=comp_db.id)
        repo.create_issue(ui_issue)
        repo.create_issue(db_issue)

        rule = ArchitecturalRule(
            name="UI cannot depend on DB",
            rule_type=RuleType.FORBIDDEN_DEPENDENCY,
            source_pattern=str(comp_ui.id),
            target_pattern=str(comp_db.id),
        )
        analyzer.add_rule(rule)

        result = analyzer.validate_dependency(str(ui_issue.id), str(db_issue.id))
        assert result.has_errors is True

    def test_max_dependency_depth_violation(self, analyzer, repo):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)

        issues = []
        for i in range(6):
            issue = Issue(title=f"Issue {i}", component_id=comp.id)
            repo.create_issue(issue)
            issues.append(issue)

        # Chain: 0 -> 1 -> 2 -> 3 -> 4 -> 5
        for i in range(5):
            repo.add_dependency(str(issues[i].id), str(issues[i + 1].id))

        rule = ArchitecturalRule(
            name="Max depth 3",
            rule_type=RuleType.MAX_DEPENDENCY_DEPTH,
            max_depth=3,
        )
        analyzer.add_rule(rule)

        result = analyzer.validate_dependency(str(issues[0].id), str(issues[1].id))
        assert result.has_errors is True

    def test_max_dependency_depth_no_violation(self, analyzer, repo):
        comp = Component(name="Backend", project="test")
        repo.create_component(comp)

        a = Issue(title="A", component_id=comp.id)
        b = Issue(title="B", component_id=comp.id)
        repo.create_issue(a)
        repo.create_issue(b)
        repo.add_dependency(str(a.id), str(b.id))

        rule = ArchitecturalRule(
            name="Max depth 3",
            rule_type=RuleType.MAX_DEPENDENCY_DEPTH,
            max_depth=3,
        )
        analyzer.add_rule(rule)

        result = analyzer.validate_dependency(str(a.id), str(b.id))
        assert result.is_valid is True

    def test_inactive_rules_are_ignored(self, analyzer):
        rule = ArchitecturalRule(
            name="Inactive",
            rule_type=RuleType.FORBIDDEN_TECHNOLOGY,
            source_pattern="sql",
            is_active=False,
        )
        analyzer.add_rule(rule)

        issue = Issue(title="Test", component_id=uuid4(), description="Uses SQL")
        result = analyzer.validate_issue_creation(issue)
        assert result.is_valid is True
