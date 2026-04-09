"""Tests for core domain entities."""

from datetime import datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from socialseed_tasker.core.task_management.entities import (
    Component,
    Issue,
    IssuePriority,
    IssueStatus,
)
from socialseed_tasker.core.task_management.value_objects import ReasoningContext, ReasoningLogEntry


class TestIssueStatus:
    def test_all_statuses_exist(self):
        assert IssueStatus.OPEN.value == "OPEN"
        assert IssueStatus.IN_PROGRESS.value == "IN_PROGRESS"
        assert IssueStatus.CLOSED.value == "CLOSED"
        assert IssueStatus.BLOCKED.value == "BLOCKED"


class TestIssuePriority:
    def test_all_priorities_exist(self):
        assert IssuePriority.LOW.value == "LOW"
        assert IssuePriority.MEDIUM.value == "MEDIUM"
        assert IssuePriority.HIGH.value == "HIGH"
        assert IssuePriority.CRITICAL.value == "CRITICAL"


class TestComponent:
    def test_create_minimal_component(self):
        component = Component(name="Backend", project="my-project")
        assert isinstance(component.id, UUID)
        assert component.name == "Backend"
        assert component.description is None
        assert component.project == "my-project"
        assert isinstance(component.created_at, datetime)
        assert isinstance(component.updated_at, datetime)

    def test_create_full_component(self):
        component = Component(
            name="API",
            description="REST API layer",
            project="socialseed",
        )
        assert component.name == "API"
        assert component.description == "REST API layer"
        assert component.project == "socialseed"

    def test_component_is_frozen(self):
        component = Component(name="Backend", project="my-project")
        with pytest.raises(ValidationError):
            component.name = "Frontend"

    def test_component_rejects_empty_name(self):
        with pytest.raises(ValidationError):
            Component(name="", project="my-project")

    def test_component_rejects_empty_project(self):
        with pytest.raises(ValidationError):
            Component(name="Backend", project="")

    def test_component_serializable(self):
        component = Component(name="Backend", project="my-project")
        data = component.model_dump(mode="json")
        assert data["name"] == "Backend"
        assert data["project"] == "my-project"
        restored = Component(**data)
        assert restored.id == component.id
        assert restored.name == component.name


class TestIssue:
    def test_create_minimal_issue(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(title="Fix login bug", component_id=component_id)
        assert isinstance(issue.id, UUID)
        assert issue.title == "Fix login bug"
        assert issue.status == IssueStatus.OPEN
        assert issue.priority == IssuePriority.MEDIUM
        assert issue.component_id == component_id
        assert issue.labels == []
        assert issue.dependencies == []
        assert issue.blocks == []
        assert issue.affects == []
        assert issue.closed_at is None
        assert issue.architectural_constraints == []

    def test_create_full_issue(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        dep_id = UUID("00000000-0000-0000-0000-000000000002")
        issue = Issue(
            title="Implement auth",
            description="Add JWT authentication",
            status=IssueStatus.IN_PROGRESS,
            priority=IssuePriority.HIGH,
            component_id=component_id,
            labels=["backend", "security"],
            dependencies=[dep_id],
            architectural_constraints=["no-sql-in-graph-module"],
        )
        assert issue.description == "Add JWT authentication"
        assert issue.status == IssueStatus.IN_PROGRESS
        assert issue.priority == IssuePriority.HIGH
        assert issue.labels == ["backend", "security"]
        assert issue.dependencies == [dep_id]
        assert issue.architectural_constraints == ["no-sql-in-graph-module"]

    def test_issue_is_frozen(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(title="Test", component_id=component_id)
        with pytest.raises(ValidationError):
            issue.title = "Changed"

    def test_issue_rejects_empty_title(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        with pytest.raises(ValidationError):
            Issue(title="", component_id=component_id)

    def test_issue_rejects_title_over_200_chars(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        with pytest.raises(ValidationError):
            Issue(title="A" * 201, component_id=component_id)

    def test_issue_accepts_title_of_200_chars(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(title="A" * 200, component_id=component_id)
        assert len(issue.title) == 200

    def test_issue_closed_at_is_none_by_default(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(title="Test", component_id=component_id)
        assert issue.closed_at is None

    def test_issue_serializable(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(title="Test", component_id=component_id)
        data = issue.model_dump(mode="json")
        assert data["title"] == "Test"
        restored = Issue(**data)
        assert restored.id == issue.id
        assert restored.title == issue.title


class TestReasoningLogEntry:
    def test_create_minimal_reasoning_log(self):
        log = ReasoningLogEntry(
            context=ReasoningContext.ARCHITECTURE_CHOICE,
            reasoning="Selected Neo4j for graph-based dependency tracking",
        )
        assert isinstance(log.id, UUID)
        assert log.context == ReasoningContext.ARCHITECTURE_CHOICE
        assert log.reasoning == "Selected Neo4j for graph-based dependency tracking"
        assert log.related_nodes == []
        assert isinstance(log.timestamp, datetime)

    def test_create_full_reasoning_log(self):
        related_id = UUID("00000000-0000-0000-0000-000000000001")
        log = ReasoningLogEntry(
            context=ReasoningContext.COMPONENT_SELECTION,
            reasoning="Chose auth-service for authentication features",
            related_nodes=[related_id],
        )
        assert log.context == ReasoningContext.COMPONENT_SELECTION
        assert log.related_nodes == [related_id]

    def test_reasoning_log_is_frozen(self):
        log = ReasoningLogEntry(
            context=ReasoningContext.DEPENDENCY_ANALYSIS,
            reasoning="Test reasoning",
        )
        with pytest.raises(ValidationError):
            log.reasoning = "Changed"

    def test_all_reasoning_contexts_exist(self):
        assert ReasoningContext.COMPONENT_SELECTION.value == "component_selection"
        assert ReasoningContext.DEPENDENCY_ANALYSIS.value == "dependency_analysis"
        assert ReasoningContext.ARCHITECTURE_CHOICE.value == "architecture_choice"
        assert ReasoningContext.IMPACT_ASSESSMENT.value == "impact_assessment"
        assert ReasoningContext.PRIORITY_DECISION.value == "priority_decision"


class TestIssueWithReasoningLogs:
    def test_issue_with_reasoning_logs(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        log = ReasoningLogEntry(
            context=ReasoningContext.ARCHITECTURE_CHOICE,
            reasoning="Selected microservices architecture for scalability",
        )
        issue = Issue(
            title="Design system architecture",
            component_id=component_id,
            reasoning_logs=[log],
        )
        assert len(issue.reasoning_logs) == 1
        assert issue.reasoning_logs[0].context == ReasoningContext.ARCHITECTURE_CHOICE

    def test_issue_reasoning_logs_default_empty(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(title="Test", component_id=component_id)
        assert issue.reasoning_logs == []

    def test_issue_with_multiple_reasoning_logs(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        log1 = ReasoningLogEntry(
            context=ReasoningContext.COMPONENT_SELECTION,
            reasoning="Selected backend component",
        )
        log2 = ReasoningLogEntry(
            context=ReasoningContext.DEPENDENCY_ANALYSIS,
            reasoning="Analyzed dependencies between services",
        )
        issue = Issue(
            title="Project setup",
            component_id=component_id,
            reasoning_logs=[log1, log2],
        )
        assert len(issue.reasoning_logs) == 2
        assert issue.reasoning_logs[0].context == ReasoningContext.COMPONENT_SELECTION
        assert issue.reasoning_logs[1].context == ReasoningContext.DEPENDENCY_ANALYSIS


class TestIssueManifest:
    def test_issue_with_manifest_todo(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(
            title="Test issue",
            component_id=component_id,
            manifest_todo=[{"task": "Implement feature", "completed": "false"}],
        )
        assert len(issue.manifest_todo) == 1
        assert issue.manifest_todo[0]["task"] == "Implement feature"

    def test_issue_with_manifest_files(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(
            title="Test issue",
            component_id=component_id,
            manifest_files=["src/core/module.ts", "tests/test_module.py"],
        )
        assert len(issue.manifest_files) == 2
        assert "src/core/module.ts" in issue.manifest_files

    def test_issue_with_manifest_notes(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(
            title="Test issue",
            component_id=component_id,
            manifest_notes=["Temporary workaround", "TODO: refactor"],
        )
        assert len(issue.manifest_notes) == 2
        assert "Temporary workaround" in issue.manifest_notes

    def test_issue_manifest_defaults_empty(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(title="Test", component_id=component_id)
        assert issue.manifest_todo == []
        assert issue.manifest_files == []
        assert issue.manifest_notes == []

    def test_issue_with_full_manifest(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(
            title="Test issue",
            component_id=component_id,
            manifest_todo=[{"task": "Step 1", "completed": "true"}],
            manifest_files=["src/main.py"],
            manifest_notes=["Note 1"],
        )
        assert len(issue.manifest_todo) == 1
        assert len(issue.manifest_files) == 1
        assert len(issue.manifest_notes) == 1


class TestAgentLifecycle:
    def test_issue_with_agent_lifecycle_fields(self):
        from datetime import datetime

        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(
            title="Test issue",
            component_id=component_id,
            agent_working=True,
            agent_started_at=datetime.now(),
            agent_id="agent-001",
        )
        assert issue.agent_working == True
        assert issue.agent_started_at is not None
        assert issue.agent_id == "agent-001"

    def test_issue_agent_lifecycle_defaults(self):
        component_id = UUID("00000000-0000-0000-0000-000000000001")
        issue = Issue(title="Test", component_id=component_id)
        assert issue.agent_working == False
        assert issue.agent_started_at is None
        assert issue.agent_finished_at is None
        assert issue.agent_id is None

    def test_issue_agent_finish_fields(self):
        from datetime import datetime

        component_id = UUID("00000000-0000-0000-0000-000000000001")
        start_time = datetime.now()
        finish_time = datetime.now()
        issue = Issue(
            title="Test issue",
            component_id=component_id,
            agent_working=False,
            agent_started_at=start_time,
            agent_finished_at=finish_time,
            agent_id="agent-001",
        )
        assert issue.agent_working == False
        assert issue.agent_started_at == start_time
        assert issue.agent_finished_at == finish_time
