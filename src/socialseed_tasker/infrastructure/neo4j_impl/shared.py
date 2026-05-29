from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel

from socialseed_tasker.domain.entities import Component, Issue, IssueStatus, ReasoningContext, ReasoningLogEntry


class _ReasoningLogEntryDTO(BaseModel):
    id: str
    timestamp: str
    context: str
    reasoning: str
    related_nodes: list[str]


def _node_to_issue(node: dict[str, Any]) -> Issue:
    """Convert a Neo4j node to a domain Issue."""
    data = dict(node)
    reasoningLogs = []
    raw_logs = data.get("reasoningLogs")
    if raw_logs:
        if isinstance(raw_logs, str):
            raw_logs = json.loads(raw_logs)
        for log_data in raw_logs:
            if isinstance(log_data, dict):
                try:
                    context_value = log_data.get("context", "architecture_choice")
                    context_enum = ReasoningContext(context_value)
                except ValueError:
                    context_enum = ReasoningContext.ARCHITECTURE_CHOICE
                reasoningLogs.append(
                    ReasoningLogEntry(
                        id=log_data.get("id"),
                        timestamp=datetime.fromisoformat(
                            log_data.get("timestamp", datetime.now(timezone.utc).isoformat())
                        ),
                        context=context_enum,
                        reasoning=log_data.get("reasoning", ""),
                        related_nodes=log_data.get("related_nodes", []),
                    )
                )
    return Issue(
        id=data.get("id") or data.get("_id", ""),
        title=data.get("title", ""),
        description=data.get("description", ""),
        status=IssueStatus(data.get("status", "OPEN")),
        priority=data.get("priority", "MEDIUM"),
        component_id=data.get("componentId") or data.get("component_id"),
        labels=data.get("labels", []),
        dependencies=data.get("dependencies", []),
        blocks=data.get("blocks", []),
        affects=data.get("affects", []),
        created_at=data.get("createdAt") or data.get("created_at") or datetime.now(timezone.utc),
        updated_at=data.get("updatedAt") or data.get("updated_at") or datetime.now(timezone.utc),
        closed_at=data.get("closedAt") or data.get("closed_at"),
        architectural_constraints=data.get("architecturalConstraints", []),
        agent_working=data.get("agentWorking", False),
        agent_started_at=data.get("agentStartedAt") or data.get("agent_started_at"),
        agent_finished_at=data.get("agentFinishedAt") or data.get("agent_finished_at"),
        agent_id=data.get("agentId") or data.get("agent_id"),
        reasoning_logs=reasoningLogs,
        manifest_todo=data.get("manifestTodo", []),
        manifest_files=data.get("manifestFiles", []),
        manifest_notes=data.get("manifestNotes", []),
        resolved_by_commit_sha=data.get("resolvedByCommitSha") or data.get("resolved_by_commit_sha"),
        resolution=data.get("resolution"),
    )


def _node_to_component(node: dict[str, Any]) -> Component:
    """Convert a Neo4j node to a domain Component."""
    data = dict(node)
    return Component(
        id=data["id"],
        name=data["name"],
        description=data.get("description"),
        project=data["project"],
        created_at=data.get("createdAt") or data.get("created_at") or datetime.now(timezone.utc),
        updated_at=data.get("updatedAt") or data.get("updated_at") or datetime.now(timezone.utc),
    )


def _to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    return "".join(word.capitalize() if i > 0 else word for i, word in enumerate(string.split("_")))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
