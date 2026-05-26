from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator
from uuid import UUID

from socialseed_tasker.application.actions import TaskRepositoryInterface
from socialseed_tasker.domain.entities import Component, Issue, IssuePriority, IssueStatus
from socialseed_tasker.infrastructure.http.api_client import ApiHttpClient


def _parse_issue(data: dict[str, Any]) -> Issue:
    raw = dict(data)
    raw["id"] = UUID(raw["id"]) if isinstance(raw.get("id"), str) else raw.get("id")
    raw["component_id"] = UUID(raw["component_id"]) if isinstance(raw.get("component_id"), str) else raw.get("component_id")
    priority_val = raw.get("priority", "MEDIUM")
    if isinstance(priority_val, str):
        raw["priority"] = IssuePriority(priority_val)
    status_val = raw.get("status", "OPEN")
    if isinstance(status_val, str):
        raw["status"] = IssueStatus(status_val)
    return Issue(**raw)


def _parse_component(data: dict[str, Any]) -> Component:
    raw = dict(data)
    raw["id"] = UUID(raw["id"]) if isinstance(raw.get("id"), str) else raw.get("id")
    return Component(**raw)


_API = "/api/v1"


class ApiTaskRepository(TaskRepositoryInterface):
    """TaskRepositoryInterface implementation that delegates to the Tasker REST API.

    Every method maps to a corresponding HTTP endpoint. Errors from the
    API are translated to domain exceptions via ApiHttpClient.
    """

    def __init__(self, client: ApiHttpClient) -> None:
        self.client = client

    # -- Issue CRUD ----------------------------------------------------------

    def create_issue(self, issue: Issue) -> Issue:
        data = self.client.request("POST", f"{_API}/issues", json=_issue_to_dict(issue))
        if data and "id" in data:
            return issue.model_copy(update={"id": UUID(data["id"])})
        return issue

    def get_issue(self, issue_id: str) -> Issue | None:
        data = self.client.request("GET", f"{_API}/issues/{issue_id}")
        if data is None:
            return None
        return _parse_issue(data)

    def update_issue(self, issue_id: str, updates: dict) -> Issue:
        data = self.client.request("PATCH", f"{_API}/issues/{issue_id}", json=updates)
        return _parse_issue(data)

    def close_issue(self, issue_id: str, commit_sha: str | None = None, resolution: str = "implemented") -> Issue:
        data = self.client.request(
            "POST",
            f"{_API}/issues/{issue_id}/close",
            json={"commit_sha": commit_sha, "resolution": resolution},
        )
        return _parse_issue(data)

    def delete_issue(self, issue_id: str) -> None:
        self.client.request("DELETE", f"{_API}/issues/{issue_id}")

    def list_issues(
        self,
        component_id: str | None = None,
        statuses: list[str] | None = None,
        project: str | None = None,
    ) -> list[Issue]:
        params: dict[str, Any] = {}
        if component_id:
            params["component_id"] = component_id
        if statuses:
            params["statuses"] = ",".join(statuses)
        if project:
            params["project"] = project
        items = self.client.paginate(f"{_API}/issues", params=params)
        return [_parse_issue(i) for i in items]

    # -- Dependency management -----------------------------------------------

    def add_dependency(self, issue_id: str, depends_on_id: str) -> None:
        self.client.request("POST", f"{_API}/issues/{issue_id}/dependencies", json={"depends_on_id": depends_on_id})

    def remove_dependency(self, issue_id: str, depends_on_id: str) -> None:
        self.client.request("DELETE", f"{_API}/issues/{issue_id}/dependencies/{depends_on_id}")

    def get_dependencies(self, issue_id: str) -> list[Issue]:
        items = self.client.paginate(f"{_API}/issues/{issue_id}/dependencies")
        return [_parse_issue(i) for i in items]

    def get_dependents(self, issue_id: str) -> list[Issue]:
        data = self.client.request("GET", f"{_API}/issues/{issue_id}/dependents")
        if isinstance(data, list):
            return [_parse_issue(i) for i in data]
        if isinstance(data, dict):
            items = data.get("items", data.get("data", []))
            return [_parse_issue(i) for i in items]
        return []

    def get_blocked_issues(self) -> list[Issue]:
        data = self.client.request("GET", f"{_API}/blocked-issues")
        if isinstance(data, list):
            return [_parse_issue(i) for i in data]
        if isinstance(data, dict):
            items = data.get("items", data.get("data", []))
            return [_parse_issue(i) for i in items]
        return []

    def get_workable_issues(
        self,
        priority: str | None = None,
        component_id: str | None = None,
    ) -> list[Issue]:
        params: dict[str, Any] = {}
        if priority:
            params["priority"] = priority
        if component_id:
            params["component"] = component_id
        data = self.client.request("GET", f"{_API}/workable-issues", params=params)
        if isinstance(data, list):
            return [_parse_issue(i) for i in data]
        if isinstance(data, dict):
            items = data.get("items", data.get("data", []))
            return [_parse_issue(i) for i in items]
        return []

    # -- CodeSymbol relationship (AFFECTS) -----------------------------------

    def add_affects_symbol(self, issue_id: str, symbol_id: str) -> None:
        self.client.request("POST", f"{_API}/issues/{issue_id}/affects", json={"symbol_id": symbol_id})

    def get_affected_symbols(self, issue_id: str) -> list[dict[str, Any]]:
        data = self.client.request("GET", f"{_API}/issues/{issue_id}/affects")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return []

    def get_issues_affecting_symbol(self, symbol_id: str) -> list[Issue]:
        data = self.client.request("GET", f"{_API}/code/symbols/{symbol_id}/issues")
        if isinstance(data, list):
            return [_parse_issue(i) for i in data]
        if isinstance(data, dict):
            items = data.get("items", data.get("data", []))
            return [_parse_issue(i) for i in items]
        return []

    def remove_affects_symbol(self, issue_id: str, symbol_id: str) -> None:
        self.client.request("DELETE", f"{_API}/issues/{issue_id}/affects", json={"symbol_id": symbol_id})

    # -- Component CRUD ------------------------------------------------------

    def create_component(self, component: Component) -> Component:
        data = self.client.request("POST", f"{_API}/components", json=_component_to_dict(component))
        if data and "id" in data:
            return component.model_copy(update={"id": UUID(data["id"])})
        return component

    def get_component(self, component_id: str) -> Component | None:
        data = self.client.request("GET", f"{_API}/components/{component_id}")
        if data is None:
            return None
        return _parse_component(data)

    def list_components(self, project: str | None = None) -> list[Component]:
        params = {"project": project} if project else None
        items = self.client.paginate(f"{_API}/components", params=params)
        return [_parse_component(i) for i in items]

    def update_component(self, component_id: str, updates: dict) -> Component:
        data = self.client.request("PATCH", f"{_API}/components/{component_id}", json=updates)
        return _parse_component(data)

    def delete_component(self, component_id: str) -> None:
        self.client.request("DELETE", f"{_API}/components/{component_id}")

    def add_component_dependency(self, component_id: str, depends_on_id: str) -> None:
        self.client.request(
            "POST",
            f"{_API}/components/{component_id}/dependencies",
            json={"depends_on_id": depends_on_id},
        )

    def remove_component_dependency(self, component_id: str, depends_on_id: str) -> None:
        self.client.request("DELETE", f"{_API}/components/{component_id}/dependencies/{depends_on_id}")

    def get_component_dependencies(self, component_id: str) -> list[Component]:
        data = self.client.request("GET", f"{_API}/components/{component_id}/dependencies")
        if isinstance(data, list):
            return [_parse_component(i) for i in data]
        if isinstance(data, dict):
            items = data.get("items", data.get("data", []))
            return [_parse_component(i) for i in items]
        return []

    def get_component_dependents(self, component_id: str) -> list[Component]:
        data = self.client.request("GET", f"{_API}/components/{component_id}/dependents")
        if isinstance(data, list):
            return [_parse_component(i) for i in data]
        if isinstance(data, dict):
            items = data.get("items", data.get("data", []))
            return [_parse_component(i) for i in items]
        return []

    # -- Project discovery --------------------------------------------------

    def list_projects(self) -> list[str]:
        data = self.client.request("GET", f"{_API}/projects")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            items = data.get("items", data.get("data", []))
            return items if isinstance(items, list) else []
        return []

    def create_epic(self, epic: Any) -> None:
        self.client.request("POST", f"{_API}/epics", json=_to_dict(epic))

    def get_epic(self, epic_id: str) -> Any | None:
        return self.client.request("GET", f"{_API}/epics/{epic_id}")

    def list_epics(self) -> list[Any]:
        data = self.client.request("GET", f"{_API}/epics")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return []

    def update_epic(self, epic_id: str, updates: dict) -> Any:
        return self.client.request("PATCH", f"{_API}/epics/{epic_id}", json=updates)

    def delete_epic(self, epic_id: str) -> None:
        self.client.request("DELETE", f"{_API}/epics/{epic_id}")

    def link_issue_to_epic(self, issue_id: str, epic_id: str) -> None:
        self.client.request("POST", f"{_API}/epics/{epic_id}/issues/{issue_id}")

    def create_objective(self, objective: Any) -> None:
        self.client.request("POST", f"{_API}/objectives", json=_to_dict(objective))

    def get_objective(self, objective_id: str) -> Any | None:
        return self.client.request("GET", f"{_API}/objectives/{objective_id}")

    def list_objectives(self) -> list[Any]:
        data = self.client.request("GET", f"{_API}/objectives")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return []

    def update_objective(self, objective_id: str, updates: dict) -> Any:
        return self.client.request("PATCH", f"{_API}/objectives/{objective_id}", json=updates)

    def delete_objective(self, objective_id: str) -> None:
        self.client.request("DELETE", f"{_API}/objectives/{objective_id}")

    def link_epic_to_objective(self, epic_id: str, objective_id: str) -> None:
        self.client.request("POST", f"{_API}/objectives/{objective_id}/epics/{epic_id}")

    def get_component_by_name(self, name: str, project: str | None = None) -> Component | None:
        params: dict[str, Any] = {"name": name}
        if project:
            params["project"] = project
        data = self.client.request("GET", f"{_API}/components", params=params)
        if data is None:
            return None
        if isinstance(data, dict):
            items = data.get("items", data.get("data", []))
        elif isinstance(data, list):
            items = data
        else:
            items = []
        if items:
            return _parse_component(items[0])
        return None

    def find_issues_by_title(
        self,
        title: str,
        component_id: str | None = None,
    ) -> list[Issue]:
        params: dict[str, Any] = {"title": title}
        if component_id:
            params["component_id"] = component_id
        items = self.client.paginate(f"{_API}/issues", params=params)
        return [_parse_issue(i) for i in items]

    # -- Reasoning log ---------------------------------------------------------

    def add_reasoning_log(
        self,
        issue_id: str,
        context: str,
        reasoning: str,
        related_nodes: list[str] | None = None,
    ) -> Issue:
        data = self.client.request(
            "POST",
            f"{_API}/issues/{issue_id}/reasoning",
            json={
                "context": context,
                "reasoning": reasoning,
                "related_nodes": related_nodes or [],
            },
        )
        return _parse_issue(data)

    def get_reasoning_logs(self, issue_id: str) -> list[dict[str, Any]]:
        data = self.client.request("GET", f"{_API}/issues/{issue_id}/reasoning")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return []

    # -- Manifest ---------------------------------------------------------------

    def update_manifest_todo(self, issue_id: str, todo: list[dict[str, str]]) -> Issue:
        data = self.client.request("PATCH", f"{_API}/issues/{issue_id}/manifest/todo", json={"todo": todo})
        return _parse_issue(data)

    def update_manifest_files(self, issue_id: str, files: list[str]) -> Issue:
        data = self.client.request("PATCH", f"{_API}/issues/{issue_id}/manifest/files", json={"files": files})
        return _parse_issue(data)

    def update_manifest_notes(self, issue_id: str, notes: list[str]) -> Issue:
        data = self.client.request("PATCH", f"{_API}/issues/{issue_id}/manifest/notes", json={"notes": notes})
        return _parse_issue(data)

    def get_manifest(self, issue_id: str) -> dict[str, Any]:
        data = self.client.request("GET", f"{_API}/issues/{issue_id}/manifest")
        if isinstance(data, dict):
            return data
        return {}

    # -- Agent lifecycle --------------------------------------------------------

    def start_agent_work(self, issue_id: str, agent_id: str) -> Issue:
        data = self.client.request(
            "POST",
            f"{_API}/issues/{issue_id}/agent/start",
            json={"agent_id": agent_id},
        )
        return _parse_issue(data)

    def finish_agent_work(self, issue_id: str) -> Issue:
        data = self.client.request("POST", f"{_API}/issues/{issue_id}/agent/finish")
        return _parse_issue(data)

    def get_agent_status(self, issue_id: str) -> dict[str, Any]:
        data = self.client.request("GET", f"{_API}/issues/{issue_id}/agent/status")
        if isinstance(data, dict):
            return {
                "agent_working": data.get("agent_working", False),
                "agent_started_at": data.get("agent_started_at"),
                "agent_finished_at": data.get("agent_finished_at"),
                "agent_id": data.get("agent_id"),
            }
        return {}

    # -- Cost analytics ---------------------------------------------------------

    def get_cost_per_component(self) -> list[dict]:
        data = self.client.request("GET", f"{_API}/cost/component")
        if isinstance(data, list):
            return data
        return []

    def get_cost_per_epic(self) -> list[dict]:
        data = self.client.request("GET", f"{_API}/cost/epic")
        if isinstance(data, list):
            return data
        return []

    def get_cost_per_project(self) -> list[dict]:
        data = self.client.request("GET", f"{_API}/cost/project")
        if isinstance(data, list):
            return data
        return []

    def get_cost_summary(self) -> dict:
        data = self.client.request("GET", f"{_API}/cost/summary")
        if isinstance(data, dict):
            return data
        return {}

    # -- Deployments ------------------------------------------------------------

    def get_deployments(self, environment_name: str | None = None, limit: int = 50) -> list[dict]:
        params: dict[str, Any] = {"limit": limit}
        if environment_name:
            params["environment"] = environment_name
        data = self.client.request("GET", f"{_API}/deployments", params=params)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return []

    def get_issue_deployments(self, issue_id: str) -> list[dict]:
        data = self.client.request("GET", f"{_API}/issues/{issue_id}/deployments")
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return []

    def create_deployment(self, deployment: Any) -> None:
        self.client.request("POST", f"{_API}/deployments", json=_to_dict(deployment))

    # -- Vector search ----------------------------------------------------------

    def search_by_embedding(self, embedding: list[float], threshold: float = 0.7, limit: int = 10) -> list[dict]:
        data = self.client.request(
            "POST",
            f"{_API}/issues/search",
            json={"embedding": embedding, "threshold": threshold, "limit": limit},
        )
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return []

    def find_similar_issues(self, issue_id: str, threshold: float = 0.7, limit: int = 10) -> list[dict]:
        data = self.client.request(
            "GET",
            f"{_API}/issues/{issue_id}/similar",
            params={"threshold": threshold, "limit": limit},
        )
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return []

    def update_issue_embedding(self, issue_id: str, embedding: list[float]) -> None:
        self.client.request("POST", f"{_API}/issues/{issue_id}/embedding", json={"embedding": embedding})

    # -- Constraints -----------------------------------------------------------

    def create_constraint(self, constraint: Any) -> None:
        self.client.request("POST", f"{_API}/constraints", json=_to_dict(constraint))

    def list_constraints(self, category: str | None = None) -> list[Any]:
        params = {"category": category} if category else None
        data = self.client.request("GET", f"{_API}/constraints", params=params)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("items", data.get("data", []))
        return []

    def get_constraint(self, constraint_id: str) -> Any | None:
        return self.client.request("GET", f"{_API}/constraints/{constraint_id}")

    def delete_constraint(self, constraint_id: str) -> None:
        self.client.request("DELETE", f"{_API}/constraints/{constraint_id}")

    def update_constraint(self, constraint_id: str, updates: dict) -> Any:
        return self.client.request("PATCH", f"{_API}/constraints/{constraint_id}", json=updates)

    def reset_data(self, scope: str = "all") -> dict[str, int]:
        data = self.client.request("POST", f"{_API}/admin/reset", json={"scope": scope})
        if isinstance(data, dict):
            return data
        return {}

    # -- Transactions (no-op for API mode) ---------------------------------------

    @contextmanager
    def transaction(self) -> Iterator[None]:
        yield


def _issue_to_dict(issue: Issue) -> dict[str, Any]:
    return {
        "id": str(issue.id),
        "title": issue.title,
        "description": issue.description,
        "status": issue.status.value if hasattr(issue.status, "value") else issue.status,
        "priority": issue.priority.value if hasattr(issue.priority, "value") else issue.priority,
        "component_id": str(issue.component_id),
        "labels": issue.labels,
        "dependencies": [str(d) for d in issue.dependencies],
        "blocks": [str(b) for b in issue.blocks],
        "affects": [str(a) for a in issue.affects],
    }


def _component_to_dict(component: Component) -> dict[str, Any]:
    return {
        "id": str(component.id),
        "name": component.name,
        "description": component.description or "",
        "project": component.project,
        "labels": component.labels,
    }


def _to_dict(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    if isinstance(obj, dict):
        return obj
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
