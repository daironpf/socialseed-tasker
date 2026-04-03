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
