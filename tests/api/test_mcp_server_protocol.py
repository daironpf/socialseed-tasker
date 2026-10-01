"""Real MCP server over streamable HTTP: protocol, tools and inspector audit (issue #535)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from socialseed_tasker.domain.entities import Component, Issue, IssueStatus
from socialseed_tasker.entrypoints import mcp_server as mcp_server_module
from socialseed_tasker.entrypoints.mcp_server import MCP_TOOL_NAMES
from socialseed_tasker.infrastructure.web_api.app import create_app

_UNIT_DIR = Path(__file__).resolve().parent.parent / "unit"


@pytest.fixture()
def repo():
    if str(_UNIT_DIR) not in sys.path:
        sys.path.insert(0, str(_UNIT_DIR))
    from test_api import MockRepository

    class GraphMockRepository(MockRepository):
        def __init__(self) -> None:
            super().__init__()
            self._component_deps: dict[str, set[str]] = {}

        def get_component_dependencies(self, component_id: str) -> list[Component]:
            ids = self._component_deps.get(component_id, set())
            return [self._components[cid] for cid in ids if cid in self._components]

        def get_component_dependents(self, component_id: str) -> list[Component]:
            dependents = []
            for cid, deps in self._component_deps.items():
                if component_id in deps and cid in self._components:
                    dependents.append(self._components[cid])
            return dependents

    repository = GraphMockRepository()
    comp_a = repository.create_component(Component(name="backend", project="demo"))
    comp_b = repository.create_component(Component(name="frontend", project="demo"))
    repository._component_deps[str(comp_a.id)] = {str(comp_b.id)}
    dependency = repository.create_issue(Issue(title="Base prerequisite", component_id=comp_b.id))
    blocked = repository.create_issue(Issue(title="Blocked feature", component_id=comp_a.id))
    repository.add_dependency(str(blocked.id), str(dependency.id))
    repository.create_issue(
        Issue(title="Shipped already", component_id=comp_a.id, status=IssueStatus.CLOSED)
    )
    repository.seed = {
        "comp_a": str(comp_a.id),
        "comp_b": str(comp_b.id),
        "dependency": str(dependency.id),
        "blocked": str(blocked.id),
    }
    return repository


@pytest.fixture()
def client(repo):
    with TestClient(create_app(repository=repo, neo4j_driver=object())) as test_client:
        yield test_client


def _initialize(test_client: TestClient) -> dict[str, Any]:
    response = test_client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "protocol-tests", "version": "1.0"},
            },
        },
    )
    assert response.status_code == 200
    notification = test_client.post(
        "/mcp", json={"jsonrpc": "2.0", "method": "notifications/initialized"}
    )
    assert notification.status_code == 202
    return response.json()


def _rpc(
    test_client: TestClient,
    method: str,
    params: dict[str, Any] | None = None,
    request_id: int = 2,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id, "method": method}
    if params is not None:
        body["params"] = params
    response = test_client.post("/mcp", json=body, headers=headers or {})
    assert response.status_code == 200
    return response.json()


def _call_tool(
    test_client: TestClient,
    name: str,
    arguments: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    payload = _rpc(test_client, "tools/call", {"name": name, "arguments": arguments}, headers=headers)
    result = payload["result"]
    assert result.get("isError") is not True, result["content"][0]["text"]
    return json.loads(result["content"][0]["text"])


def test_initialize_handshake(client):
    payload = _initialize(client)
    assert payload["result"]["serverInfo"]["name"] == "SocialSeed Tasker"
    assert payload["result"]["protocolVersion"]
    assert "tools" in payload["result"]["capabilities"]


def test_tools_list_exposes_the_graph_tool_set(client):
    _initialize(client)
    payload = _rpc(client, "tools/list", {})
    tools = {tool["name"]: tool for tool in payload["result"]["tools"]}
    assert set(tools) == set(MCP_TOOL_NAMES)
    for tool in tools.values():
        assert tool["description"]
        assert tool["inputSchema"]["type"] == "object"
    assert "issue_id" in tools["issue_detail"]["inputSchema"]["required"]
    assert "issue_id" in tools["dependency_impact"]["inputSchema"]["required"]
    assert "project" not in tools["blocked_issues"]["inputSchema"].get("properties", {})


def test_list_components_and_graph_architecture(client, repo):
    _initialize(client)
    components = _call_tool(client, "list_components", {})
    assert components["count"] == 2
    assert {c["name"] for c in components["components"]} == {"backend", "frontend"}

    graph = _call_tool(client, "graph_architecture", {})
    assert graph["totals"] == {"components": 2, "edges": 1, "issues": 3}
    assert graph["edges"] == [
        {"source": repo.seed["comp_a"], "target": repo.seed["comp_b"], "type": "DEPENDS_ON"}
    ]
    nodes = {node["id"]: node for node in graph["nodes"]}
    assert nodes[repo.seed["comp_a"]]["issueCount"] == 2
    assert nodes[repo.seed["comp_a"]]["openIssueCount"] == 1
    assert nodes[repo.seed["comp_b"]]["openIssueCount"] == 1


def test_blocked_issues_reports_open_blockers(client, repo):
    _initialize(client)
    data = _call_tool(client, "blocked_issues", {})
    assert data["count"] == 1
    issue = data["issues"][0]
    assert issue["id"] == repo.seed["blocked"]
    assert issue["blockedBy"] == [{"id": repo.seed["dependency"], "title": "Base prerequisite"}]


def test_issue_detail_and_dependency_impact(client, repo):
    _initialize(client)
    detail = _call_tool(client, "issue_detail", {"issue_id": repo.seed["blocked"]})
    assert detail["issue"]["title"] == "Blocked feature"
    assert detail["issue"]["status"] == "OPEN"
    assert [d["id"] for d in detail["issue"]["dependencies"]] == [repo.seed["dependency"]]

    impact = _call_tool(client, "dependency_impact", {"issue_id": repo.seed["dependency"]})
    assert impact["issueId"] == repo.seed["dependency"]
    assert impact["riskLevel"]
    affected = {i["id"] for i in impact["directlyAffected"]} | {
        i["id"] for i in impact["transitivelyAffected"]
    }
    assert repo.seed["blocked"] in affected


def test_active_policies_returns_only_active_entries(client, monkeypatch):
    from socialseed_tasker.application.policy import Policy

    active = Policy(name="guard-architecture", is_active=True)
    inactive = Policy(name="legacy-rule", is_active=False)

    class StubPolicyRepository:
        def __init__(self, driver: Any) -> None:
            self.driver = driver

        def list_policies(self) -> list[Policy]:
            return [active, inactive]

    monkeypatch.setattr(mcp_server_module, "PolicyRepository", StubPolicyRepository)
    _initialize(client)
    data = _call_tool(client, "active_policies", {})
    assert data["count"] == 1
    assert data["policies"][0]["name"] == "guard-architecture"
    assert data["policies"][0]["isActive"] is True


def test_unknown_tool_and_missing_argument_report_errors(client):
    _initialize(client)
    payload = _rpc(client, "tools/call", {"name": "does_not_exist", "arguments": {}})
    assert payload["result"]["isError"] is True

    payload = _rpc(client, "tools/call", {"name": "issue_detail", "arguments": {}})
    assert payload["result"]["isError"] is True
    assert "issue_id" in payload["result"]["content"][0]["text"]

    payload = _rpc(client, "tools/call", {"name": "issue_detail", "arguments": {"issue_id": "nope"}})
    assert payload["result"]["isError"] is True


def test_external_calls_and_sessions_reach_the_inspector(client):
    _initialize(client)
    _call_tool(client, "blocked_issues", {}, headers={"User-Agent": "Cursor-Test/1.0"})

    servers = client.get("/api/v1/mcp/servers").json()["data"]
    tasker_server = [s for s in servers if s["id"] == "tasker-mcp"]
    assert tasker_server and set(tasker_server[0]["tools"]) == set(MCP_TOOL_NAMES)
    assert tasker_server[0]["transport"] == "http"
    assert tasker_server[0]["url"] == "/mcp"

    calls = client.get("/api/v1/mcp/tool-calls").json()["data"]
    recorded = [c for c in calls if c["tool"] == "blocked_issues"]
    assert recorded and recorded[0]["server"] == "tasker-mcp"
    assert recorded[0]["status"] == "success"
    assert recorded[0]["sessionId"]

    sessions = client.get("/api/v1/mcp/sessions").json()["data"]
    external = [s for s in sessions if s["clientType"] == "external"]
    assert external and external[0]["clientName"] == "Cursor-Test/1.0"
    assert external[0]["server"] == "tasker-mcp"


def test_failed_tool_call_is_recorded_as_error(client):
    _initialize(client)
    _rpc(client, "tools/call", {"name": "issue_detail", "arguments": {"issue_id": "missing"}})
    calls = client.get("/api/v1/mcp/tool-calls").json()["data"]
    failed = [c for c in calls if c["tool"] == "issue_detail"]
    assert failed and failed[0]["status"] == "error"
    assert failed[0]["error"]


def test_mcp_endpoint_requires_api_key_when_auth_enabled(monkeypatch):
    monkeypatch.setenv("TASKER_AUTH_ENABLED", "true")
    monkeypatch.setenv("TASKER_API_KEY", "mcp-secret")
    with TestClient(create_app()) as test_client:
        response = test_client.post(
            "/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "protocol-tests", "version": "1.0"},
                },
            },
        )
        assert response.status_code == 401

        response = test_client.post(
            "/mcp",
            headers={"X-API-Key": "mcp-secret"},
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "protocol-tests", "version": "1.0"},
                },
            },
        )
        assert response.status_code == 200
        assert response.json()["result"]["serverInfo"]["name"] == "SocialSeed Tasker"
