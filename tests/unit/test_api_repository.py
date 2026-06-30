from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from socialseed_tasker.domain.entities import Component, Issue, IssuePriority, IssueStatus
from socialseed_tasker.infrastructure.api_repository import ApiTaskRepository
from socialseed_tasker.infrastructure.http.api_client import ApiHttpClient


@pytest.fixture
def mock_client():
    client = MagicMock(spec=ApiHttpClient)
    return client


@pytest.fixture
def repo(mock_client):
    return ApiTaskRepository(mock_client)


def _make_issue(**overrides) -> Issue:
    data = dict(
        title="Test Issue",
        description="A test issue",
        priority=IssuePriority.MEDIUM,
        status=IssueStatus.OPEN,
        component_id=uuid4(),
        labels=[],
    )
    data.update(overrides)
    return Issue(**data)


def _make_component(**overrides) -> Component:
    data = dict(name="test-comp", project="test-project", description="Test component")
    data.update(overrides)
    return Component(**data)


# -- Issue CRUD --------------------------------------------------------------


def test_create_issue(repo, mock_client):
    issue = _make_issue()
    repo.create_issue(issue)
    mock_client.request.assert_called_once()
    args, _ = mock_client.request.call_args
    assert args[0] == "POST"
    assert args[1].endswith("/issues")


def test_get_issue_found(repo, mock_client):
    issue_id = str(uuid4())
    mock_client.request.return_value = {
        "id": issue_id,
        "title": "Found",
        "description": "",
        "status": "OPEN",
        "priority": "MEDIUM",
        "component_id": str(uuid4()),
        "labels": [],
        "dependencies": [],
        "blocks": [],
        "affects": [],
    }
    result = repo.get_issue(issue_id)
    assert result is not None
    assert result.title == "Found"


def test_get_issue_not_found(repo, mock_client):
    mock_client.request.return_value = None
    result = repo.get_issue("nonexistent")
    assert result is None


def test_update_issue(repo, mock_client):
    issue_id = str(uuid4())
    mock_client.request.return_value = {
        "id": issue_id,
        "title": "Updated",
        "description": "Updated desc",
        "status": "OPEN",
        "priority": "HIGH",
        "component_id": str(uuid4()),
        "labels": [],
        "dependencies": [],
        "blocks": [],
        "affects": [],
    }
    result = repo.update_issue(issue_id, {"title": "Updated"})
    assert result.title == "Updated"


def test_close_issue(repo, mock_client):
    issue_id = str(uuid4())
    mock_client.request.return_value = {
        "id": issue_id,
        "title": "Closed",
        "description": "",
        "status": "CLOSED",
        "priority": "MEDIUM",
        "component_id": str(uuid4()),
        "labels": [],
        "dependencies": [],
        "blocks": [],
        "affects": [],
    }
    result = repo.close_issue(issue_id, "abc123", "implemented")
    mock_client.request.assert_called_once()
    args, kwargs = mock_client.request.call_args
    assert args[0] == "POST"
    assert "close" in args[1]
    assert kwargs["json"]["commit_sha"] == "abc123"


def test_delete_issue(repo, mock_client):
    repo.delete_issue("123")
    mock_client.request.assert_called_once_with("DELETE", "/api/v1/issues/123")


def test_list_issues(repo, mock_client):
    mock_client.paginate.return_value = [
        {"id": str(uuid4()), "title": "A", "description": "", "status": "OPEN", "priority": "MEDIUM", "component_id": str(uuid4()), "labels": [], "dependencies": [], "blocks": [], "affects": []},
        {"id": str(uuid4()), "title": "B", "description": "", "status": "OPEN", "priority": "LOW", "component_id": str(uuid4()), "labels": [], "dependencies": [], "blocks": [], "affects": []},
    ]
    issues = repo.list_issues()
    assert len(issues) == 2


# -- Component CRUD ----------------------------------------------------------


def test_create_component(repo, mock_client):
    comp = _make_component()
    repo.create_component(comp)
    mock_client.request.assert_called_once()
    args, _ = mock_client.request.call_args
    assert args[0] == "POST"
    assert args[1].endswith("/components")


def test_get_component_found(repo, mock_client):
    comp_id = str(uuid4())
    mock_client.request.return_value = {
        "id": comp_id,
        "name": "test-comp",
        "description": "Test component",
        "project": "test-project",
        "labels": [],
    }
    result = repo.get_component(comp_id)
    assert result is not None
    assert result.name == "test-comp"


def test_get_component_not_found(repo, mock_client):
    mock_client.request.return_value = None
    result = repo.get_component("nonexistent")
    assert result is None


def test_list_components(repo, mock_client):
    mock_client.paginate.return_value = [
        {"id": str(uuid4()), "name": "comp1", "description": "", "project": "p1", "labels": []},
        {"id": str(uuid4()), "name": "comp2", "description": "", "project": "p2", "labels": []},
    ]
    comps = repo.list_components()
    assert len(comps) == 2


def test_update_component(repo, mock_client):
    comp_id = str(uuid4())
    mock_client.request.return_value = {
        "id": comp_id,
        "name": "updated",
        "description": "Updated",
        "project": "p1",
        "labels": [],
    }
    result = repo.update_component(comp_id, {"name": "updated"})
    assert result.name == "updated"


def test_delete_component(repo, mock_client):
    repo.delete_component("123")
    mock_client.request.assert_called_once_with("DELETE", "/api/v1/components/123")


# -- Dependencies ------------------------------------------------------------


def test_add_dependency(repo, mock_client):
    repo.add_dependency("issue-1", "issue-2")
    mock_client.request.assert_called_once()
    args, kwargs = mock_client.request.call_args
    assert args[0] == "POST"
    assert "dependencies" in args[1]
    assert kwargs["json"]["depends_on_id"] == "issue-2"


def test_remove_dependency(repo, mock_client):
    repo.remove_dependency("issue-1", "issue-2")
    mock_client.request.assert_called_once_with("DELETE", "/api/v1/issues/issue-1/dependencies/issue-2")


def test_get_dependencies(repo, mock_client):
    mock_client.paginate.return_value = [
        {"id": str(uuid4()), "title": "Dep", "description": "", "status": "OPEN", "priority": "MEDIUM", "component_id": str(uuid4()), "labels": [], "dependencies": [], "blocks": [], "affects": []},
    ]
    deps = repo.get_dependencies("issue-1")
    assert len(deps) == 1


def test_get_dependents(repo, mock_client):
    mock_client.request.return_value = [
        {"id": str(uuid4()), "title": "Dep", "description": "", "status": "OPEN", "priority": "MEDIUM", "component_id": str(uuid4()), "labels": [], "dependencies": [], "blocks": [], "affects": []},
    ]
    deps = repo.get_dependents("issue-1")
    assert len(deps) == 1


# -- Agent lifecycle ---------------------------------------------------------


def test_start_agent_work(repo, mock_client):
    issue_id = str(uuid4())
    mock_client.request.return_value = {
        "id": issue_id,
        "title": "Working",
        "description": "",
        "status": "IN_PROGRESS",
        "priority": "MEDIUM",
        "component_id": str(uuid4()),
        "labels": [],
        "dependencies": [],
        "blocks": [],
        "affects": [],
    }
    result = repo.start_agent_work(issue_id, "agent-1")
    assert result is not None
    args, kwargs = mock_client.request.call_args
    assert args[0] == "POST"
    assert "agent/start" in args[1]
    assert kwargs["json"]["agent_id"] == "agent-1"


def test_finish_agent_work(repo, mock_client):
    issue_id = str(uuid4())
    mock_client.request.return_value = {
        "id": issue_id,
        "title": "Done",
        "description": "",
        "status": "OPEN",
        "priority": "MEDIUM",
        "component_id": str(uuid4()),
        "labels": [],
        "dependencies": [],
        "blocks": [],
        "affects": [],
    }
    result = repo.finish_agent_work(issue_id, "agent-1")
    assert result is not None


# -- Manifest -----------------------------------------------------------------


def test_update_manifest_todo(repo, mock_client):
    issue_id = str(uuid4())
    mock_client.request.return_value = {"id": issue_id, "title": "T", "description": "", "status": "OPEN", "priority": "MEDIUM", "component_id": str(uuid4()), "labels": [], "dependencies": [], "blocks": [], "affects": []}
    repo.update_manifest_todo(issue_id, [{"task": "do something", "completed": "false"}])
    args, kwargs = mock_client.request.call_args
    assert "manifest/todo" in args[1]
    assert "todo" in kwargs["json"]


# -- Reasoning log ------------------------------------------------------------


def test_add_reasoning_log(repo, mock_client):
    issue_id = str(uuid4())
    mock_client.request.return_value = {"id": issue_id, "title": "R", "description": "", "status": "OPEN", "priority": "MEDIUM", "component_id": str(uuid4()), "labels": [], "dependencies": [], "blocks": [], "affects": []}
    repo.add_reasoning_log(issue_id, "test_context", "test_reasoning")
    args, kwargs = mock_client.request.call_args
    assert "reasoning" in args[1]
    assert kwargs["json"]["context"] == "test_context"


# -- Projects ----------------------------------------------------------------


def test_list_projects(repo, mock_client):
    mock_client.request.return_value = ["project-a", "project-b"]
    projects = repo.list_projects()
    assert projects == ["project-a", "project-b"]


def test_list_projects_dict_response(repo, mock_client):
    mock_client.request.return_value = {"items": ["project-a"], "data": ["project-a"]}
    projects = repo.list_projects()
    assert projects == ["project-a"]


# -- Transaction (no-op) -----------------------------------------------------


def test_transaction_noop(repo):
    with repo.transaction():
        pass


# -- Component by name -------------------------------------------------------


def test_get_component_by_name_found(repo, mock_client):
    comp_id = str(uuid4())
    mock_client.request.return_value = {"items": [{"id": comp_id, "name": "my-comp", "description": "", "project": "p1", "labels": []}]}
    result = repo.get_component_by_name("my-comp")
    assert result is not None
    assert result.name == "my-comp"


def test_get_component_by_name_not_found(repo, mock_client):
    mock_client.request.return_value = None
    result = repo.get_component_by_name("nonexistent")
    assert result is None


# -- Find issues by title ----------------------------------------------------


def test_find_issues_by_title(repo, mock_client):
    mock_client.paginate.return_value = [{"id": str(uuid4()), "title": "Bug", "description": "", "status": "OPEN", "priority": "HIGH", "component_id": str(uuid4()), "labels": [], "dependencies": [], "blocks": [], "affects": []}]
    results = repo.find_issues_by_title("Bug")
    assert len(results) == 1
    assert results[0].title == "Bug"


# -- Edge cases --------------------------------------------------------------


def test_repository_handles_empty_pagination(repo, mock_client):
    mock_client.paginate.return_value = []
    issues = repo.list_issues()
    assert issues == []


def test_repository_handles_none_component(repo, mock_client):
    mock_client.request.return_value = None
    result = repo.get_component("nonexistent")
    assert result is None
