"""MCP server exposing the SocialSeed graph over real transports (issue #535).

Two transports share one tool set:

- streamable HTTP mounted inside the API at ``/mcp`` so remote clients
  (Cursor, Claude Desktop) can connect with just a URL and the API key
- stdio via the ``tasker-mcp`` console script for local MCP clients

Every tool call observed through HTTP is pushed into an optional audit
sink, which wires it to the MCP inspector registry (#524) so external
client sessions and tool calls are visible there.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Callable
from typing import Any

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.context import Context
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette

from socialseed_tasker import __version__
from socialseed_tasker.application.actions import (
    TaskRepositoryInterface,
    get_blocked_issues_action,
)
from socialseed_tasker.application.analyzer import RootCauseAnalyzer
from socialseed_tasker.application.policy import Policy
from socialseed_tasker.domain.entities import Component, Issue
from socialseed_tasker.infrastructure.neo4j_policy_repository import PolicyRepository

logger = logging.getLogger(__name__)

MCP_SERVER_ID = "tasker-mcp"
MCP_SERVER_NAME = "SocialSeed Tasker"
MCP_HTTP_PATH = "/mcp"
MCP_TOOL_NAMES: tuple[str, ...] = (
    "graph_architecture",
    "list_components",
    "blocked_issues",
    "active_policies",
    "issue_detail",
    "dependency_impact",
)

RepoProvider = Callable[[], TaskRepositoryInterface]
DriverProvider = Callable[[], Any]
AuditSink = Callable[[dict[str, Any]], None]


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _issue_summary(issue: Issue) -> dict[str, Any]:
    return {
        "id": str(issue.id),
        "title": issue.title,
        "status": issue.status.value,
        "priority": _enum_value(issue.priority),
        "componentId": str(issue.component_id) if issue.component_id else None,
        "labels": list(issue.labels),
    }


def _component_summary(component: Component) -> dict[str, Any]:
    return {
        "id": str(component.id),
        "name": component.name,
        "description": component.description,
        "project": component.project,
        "labels": list(component.labels),
    }


def _policy_summary(policy: Policy) -> dict[str, Any]:
    return {
        "id": str(policy.id),
        "name": policy.name,
        "description": policy.description,
        "severity": _enum_value(policy.severity),
        "targetScope": _enum_value(policy.target_scope),
        "ruleCount": len(policy.rules),
        "ruleTypes": [_enum_value(rule.rule_type) for rule in policy.rules],
        "isActive": policy.is_active,
        "remediationStrategy": policy.remediation_strategy,
    }


def _session_identity(ctx: Context | None) -> tuple[str | None, str]:
    """Derive a stable inspector session id from the client User-Agent."""
    try:
        headers = ctx.headers if ctx is not None else None
        user_agent = "mcp-client"
        for key, value in (headers or {}).items():
            if str(key).lower() == "user-agent" and value:
                user_agent = str(value)
                break
        digest = hashlib.sha1(user_agent.encode("utf-8")).hexdigest()[:12]
        return f"ext-{digest}", user_agent[:120]
    except Exception:
        return None, "mcp-client"


def _record(
    tool: str,
    arguments: dict[str, Any],
    started: float,
    ctx: Context | None,
    audit: AuditSink | None,
    summary: str | None = None,
    error: str | None = None,
) -> None:
    if audit is None:
        return
    session_id, client_name = _session_identity(ctx)
    payload: dict[str, Any] = {
        "sessionId": session_id,
        "clientName": client_name,
        "server": MCP_SERVER_ID,
        "tool": tool,
        "arguments": arguments,
        "status": "error" if error is not None else "success",
        "durationMs": int((time.perf_counter() - started) * 1000),
        "resultSummary": summary[:300] if summary else None,
        "error": error,
    }
    try:
        audit(payload)
    except Exception:
        logger.warning("MCP audit sink failed for tool %s", tool, exc_info=True)


def build_mcp_server(
    repo_provider: RepoProvider,
    driver_provider: DriverProvider | None = None,
    audit: AuditSink | None = None,
) -> MCPServer[Any]:
    """Build the MCP server with the graph tools wired to a repository."""
    server: MCPServer[Any] = MCPServer[Any](
        MCP_SERVER_NAME,
        description=(
            "Query the SocialSeed Tasker graph: architecture, components, "
            "blocked issues, policies and dependency impact."
        ),
        instructions=(
            "Use these tools to explore the SocialSeed Tasker graph. "
            "Start with graph_architecture or list_components for orientation, "
            "blocked_issues for current bottlenecks, and dependency_impact to assess risk."
        ),
        version=__version__,
    )

    def _repo() -> TaskRepositoryInterface:
        repository = repo_provider()
        if repository is None:
            raise RuntimeError("Repository not available")
        return repository

    def _driver() -> Any:
        if driver_provider is None:
            return None
        return driver_provider()

    @server.tool(
        description=(
            "Component architecture as a graph: nodes are components enriched with total and open "
            "issue counts, edges are DEPENDS_ON relationships between components."
        ),
    )
    def graph_architecture(project: str | None = None, ctx: Context | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        arguments: dict[str, Any] = {"project": project}
        try:
            repository = _repo()
            components = repository.list_components(project=project)
            issues = repository.list_issues(project=project)
            counts: dict[str, dict[str, int]] = {}
            for issue in issues:
                key = str(issue.component_id) if issue.component_id else ""
                entry = counts.setdefault(key, {"total": 0, "open": 0})
                entry["total"] += 1
                if issue.status.value != "CLOSED":
                    entry["open"] += 1
            nodes = []
            for component in components:
                component_counts = counts.get(str(component.id), {"total": 0, "open": 0})
                node = _component_summary(component)
                node["issueCount"] = component_counts["total"]
                node["openIssueCount"] = component_counts["open"]
                nodes.append(node)
            edges: list[dict[str, str]] = []
            for component in components:
                for dependency in repository.get_component_dependencies(str(component.id)):
                    edges.append(
                        {"source": str(component.id), "target": str(dependency.id), "type": "DEPENDS_ON"}
                    )
        except Exception as exc:
            _record("graph_architecture", arguments, started, ctx, audit, error=str(exc))
            raise
        data = {
            "nodes": nodes,
            "edges": edges,
            "totals": {"components": len(nodes), "edges": len(edges), "issues": len(issues)},
        }
        _record(
            "graph_architecture",
            arguments,
            started,
            ctx,
            audit,
            summary=f"{len(nodes)} component(s), {len(edges)} edge(s)",
        )
        return data

    @server.tool(description="List project components, optionally filtered by project name.")
    def list_components(project: str | None = None, ctx: Context | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        arguments: dict[str, Any] = {"project": project}
        try:
            components = _repo().list_components(project=project)
        except Exception as exc:
            _record("list_components", arguments, started, ctx, audit, error=str(exc))
            raise
        _record(
            "list_components",
            arguments,
            started,
            ctx,
            audit,
            summary=f"{len(components)} component(s)",
        )
        return {"components": [_component_summary(c) for c in components], "count": len(components)}

    @server.tool(
        description=(
            "Issues that cannot start because at least one dependency is still open, "
            "each with the open blockers behind it."
        ),
    )
    def blocked_issues(ctx: Context | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            repository = _repo()
            blocked = get_blocked_issues_action(repository)
            issues = []
            for issue in blocked:
                open_blockers = [
                    dependency
                    for dependency in repository.get_dependencies(str(issue.id))
                    if dependency.status.value != "CLOSED"
                ]
                summary = _issue_summary(issue)
                summary["blockedBy"] = [
                    {"id": str(blocker.id), "title": blocker.title} for blocker in open_blockers
                ]
                issues.append(summary)
        except Exception as exc:
            _record("blocked_issues", {}, started, ctx, audit, error=str(exc))
            raise
        _record("blocked_issues", {}, started, ctx, audit, summary=f"{len(issues)} blocked issue(s)")
        return {"issues": issues, "count": len(issues)}

    @server.tool(
        description=(
            "Active governance policies (is_active) with severity, target scope and rule types. "
            "Requires a Neo4j connection."
        ),
    )
    def active_policies(ctx: Context | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        try:
            driver = _driver()
            if driver is None:
                raise RuntimeError("Neo4j driver not available; active policies require the graph database")
            policies = [p for p in PolicyRepository(driver).list_policies() if p.is_active]
        except Exception as exc:
            _record("active_policies", {}, started, ctx, audit, error=str(exc))
            raise
        _record("active_policies", {}, started, ctx, audit, summary=f"{len(policies)} active polic(ies)")
        return {"policies": [_policy_summary(p) for p in policies], "count": len(policies)}

    @server.tool(
        description=(
            "Full detail of one issue: status, priority, labels, resolution, "
            "dependencies and dependents."
        ),
    )
    def issue_detail(issue_id: str, ctx: Context | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        arguments: dict[str, Any] = {"issue_id": issue_id}
        try:
            repository = _repo()
            issue = repository.get_issue(issue_id)
            if issue is None:
                raise ValueError(f"Issue '{issue_id}' not found")
            detail = _issue_summary(issue)
            detail["description"] = issue.description
            detail["resolution"] = issue.resolution
            detail["resolvedByCommitSha"] = issue.resolved_by_commit_sha
            detail["closedAt"] = issue.closed_at.isoformat() if issue.closed_at else None
            detail["dependencies"] = [
                _issue_summary(dep) for dep in repository.get_dependencies(issue_id)
            ]
            detail["dependents"] = [
                _issue_summary(dep) for dep in repository.get_dependents(issue_id)
            ]
        except Exception as exc:
            _record("issue_detail", arguments, started, ctx, audit, error=str(exc))
            raise
        _record("issue_detail", arguments, started, ctx, audit, summary=f"issue {issue_id}")
        return {"issue": detail}

    @server.tool(
        description=(
            "Impact analysis for an issue: directly and transitively affected issues, "
            "blocked issues, affected components and the resulting risk level."
        ),
    )
    def dependency_impact(issue_id: str, ctx: Context | None = None) -> dict[str, Any]:
        started = time.perf_counter()
        arguments: dict[str, Any] = {"issue_id": issue_id}
        try:
            repository = _repo()
            issue = repository.get_issue(issue_id)
            if issue is None:
                raise ValueError(f"Issue '{issue_id}' not found")
            impact = RootCauseAnalyzer(repository).analyze_impact(issue_id)
            data = {
                "issueId": str(impact.issue_id),
                "issueTitle": issue.title,
                "riskLevel": _enum_value(impact.risk_level),
                "graphDepth": impact.graph_depth,
                "affectedComponents": list(impact.affected_components),
                "directlyAffected": [_issue_summary(i) for i in impact.directly_affected],
                "transitivelyAffected": [_issue_summary(i) for i in impact.transitively_affected],
                "blockedIssues": [_issue_summary(i) for i in impact.blocked_issues],
                "totalAffected": len(impact.directly_affected) + len(impact.transitively_affected),
            }
        except Exception as exc:
            _record("dependency_impact", arguments, started, ctx, audit, error=str(exc))
            raise
        _record(
            "dependency_impact",
            arguments,
            started,
            ctx,
            audit,
            summary=f"risk={data['riskLevel']} affected={data['totalAffected']}",
        )
        return data

    return server


def build_streamable_http_app(server: MCPServer[Any]) -> Starlette:
    """Build the streamable HTTP transport app served at ``/mcp``.

    Stateless JSON responses keep every request independent, so clients
    need nothing beyond the endpoint URL and the API key header. DNS
    rebinding protection is disabled because access is already gated by
    the API's own auth middleware and clients reach the server through
    Docker hostnames.
    """
    return server.streamable_http_app(
        streamable_http_path=MCP_HTTP_PATH,
        json_response=True,
        stateless_http=True,
        transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
    )


def main() -> None:
    """Run the MCP server over stdio for local clients (Cursor, Claude Desktop)."""
    from socialseed_tasker.application.container import Container

    container = Container.from_env()
    repository = container.get_repository()
    driver = getattr(container, "_neo4j_driver", None)
    server = build_mcp_server(
        repo_provider=lambda: repository,
        driver_provider=lambda: driver,
    )
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
