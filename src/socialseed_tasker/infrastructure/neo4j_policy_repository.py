"""Policy Repository - Neo4j storage for Policy entities.

Provides CRUD operations and relationship management for policies.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from socialseed_tasker.application.policy import Policy, PolicySeverity, PolicyTargetScope
from socialseed_tasker.infrastructure import neo4j_queries as queries


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _policy_to_dict(policy: Policy) -> dict[str, Any]:
    """Convert a Policy to a dictionary for Neo4j."""
    return {
        "id": str(policy.id),
        "name": policy.name,
        "description": policy.description,
        "rules": json.dumps([r.model_dump() for r in policy.rules]),
        "severity": policy.severity.value if hasattr(policy.severity, 'value') else str(policy.severity),
        "target_scope": policy.target_scope.value,
        "logic_definition": policy.logic_definition,
        "remediation_strategy": policy.remediation_strategy,
        "autofix_template": policy.autofix_template,
        "is_active": policy.is_active,
        "createdAt": policy.created_at.isoformat(),
        "updatedAt": policy.updated_at.isoformat(),
    }


def _node_to_policy(node: dict[str, Any]) -> Policy:
    """Convert a Neo4j node to a domain Policy."""
    from socialseed_tasker.application.policy import PolicyRule

    rules = []
    if node.get("rules"):
        try:
            rules_data = json.loads(node["rules"])
            rules = [PolicyRule(**r) for r in rules_data]
        except (json.JSONDecodeError, TypeError):
            pass

    return Policy(
        id=UUID(node["id"]),
        name=node["name"],
        description=node.get("description", ""),
        severity=PolicySeverity(node.get("severity", "WARNING")),
        rules=rules,
        target_scope=PolicyTargetScope(node.get("targetScope") or node.get("target_scope", "COMPONENT")),
        logic_definition=node.get("logicDefinition") or node.get("logic_definition"),
        remediation_strategy=node.get("remediationStrategy") or node.get("remediation_strategy"),
        autofix_template=node.get("autofixTemplate") or node.get("autofix_template"),
        is_active=node.get("isActive", True),
        created_at=datetime.fromisoformat(node.get("createdAt") or node.get("created_at", datetime.now(timezone.utc).isoformat())),
        updated_at=datetime.fromisoformat(node.get("updatedAt") or node.get("updated_at", datetime.now(timezone.utc).isoformat())),
    )


class PolicyRepository:
    """Repository for Policy entities in Neo4j."""

    def __init__(self, driver: Any) -> None:
        self._driver = driver

    def _get_session(self):
        """Get Neo4j session."""
        if hasattr(self._driver, "driver"):
            return self._driver.driver.session(database=self._driver.database)
        return self._driver.session(database="neo4j")

    def create_policy(self, policy: Policy) -> None:
        """Create a new Policy node in Neo4j."""
        with self._get_session() as session:
            session.run(
                queries.CREATE_POLICY,
                **_policy_to_dict(policy),
            )

    def get_policy(self, policy_id: str) -> Policy | None:
        """Get a policy by ID."""
        with self._get_session() as session:
            result = session.run(queries.GET_POLICY, id=policy_id)
            record = result.single()
            return _node_to_policy(record["p"]) if record else None

    def get_policy_by_name(self, name: str) -> Policy | None:
        """Get a policy by name."""
        with self._get_session() as session:
            result = session.run(queries.GET_POLICY_BY_NAME, name=name)
            record = result.single()
            return _node_to_policy(record["p"]) if record else None

    def update_policy(self, policy_id: str, updates: dict[str, Any]) -> Policy:
        """Update policy properties."""
        with self._get_session() as session:
            result = session.run(
                queries.UPDATE_POLICY,
                id=policy_id,
                updates=updates,
                updated_at=_now_iso(),
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Policy {policy_id} not found")
            return _node_to_policy(record["p"])

    def delete_policy(self, policy_id: str) -> None:
        """Delete a policy from Neo4j."""
        with self._get_session() as session:
            session.run(queries.DELETE_POLICY, id=policy_id)

    def list_policies(
        self,
        severity: str | None = None,
        target_scope: str | None = None,
        is_active: bool | None = None,
        limit: int = 50,
    ) -> list[Policy]:
        """List policies with optional filters."""
        with self._get_session() as session:
            result = session.run(
                queries.LIST_POLICIES,
                severity=severity,
                target_scope=target_scope,
                is_active=is_active,
                limit=limit,
            )
            return [_node_to_policy(r["p"]) for r in result]

    def link_policy_to_project(self, policy_id: str, project_id: str) -> None:
        """Create (Project)-[:ENFORCES]->(Policy) relationship."""
        with self._get_session() as session:
            session.run(
                queries.LINK_POLICY_TO_PROJECT,
                policy_id=policy_id,
                projectId=project_id,
            )

    def link_policy_to_agent(self, policy_id: str, agent_id: str) -> None:
        """Create (Agent)-[:MUST_COMPLY_WITH]->(Policy) relationship."""
        with self._get_session() as session:
            session.run(
                queries.LINK_POLICY_TO_AGENT,
                policy_id=policy_id,
                agent_id=agent_id,
            )

    def link_policy_to_component(self, policy_id: str, component_id: str) -> None:
        """Create (Policy)-[:APPLIES_TO]->(Component) relationship."""
        with self._get_session() as session:
            session.run(
                queries.LINK_POLICY_TO_COMPONENT,
                policy_id=policy_id,
                component_id=component_id,
            )

    def get_policies_for_project(self, project_id: str, limit: int = 50) -> list[Policy]:
        """Get all policies enforced by a project."""
        with self._get_session() as session:
            result = session.run(
                queries.GET_POLICIES_FOR_PROJECT,
                project_id=project_id,
                limit=limit,
            )
            return [_node_to_policy(r["p"]) for r in result]

    def get_policies_for_agent(self, agent_id: str, limit: int = 50) -> list[Policy]:
        """Get all policies an agent must comply with."""
        with self._get_session() as session:
            result = session.run(
                queries.GET_POLICIES_FOR_AGENT,
                agent_id=agent_id,
                limit=limit,
            )
            return [_node_to_policy(r["p"]) for r in result]

    def get_policies_for_component(self, component_id: str, limit: int = 50) -> list[Policy]:
        """Get all policies that apply to a component."""
        with self._get_session() as session:
            result = session.run(
                queries.GET_POLICIES_FOR_COMPONENT,
                component_id=component_id,
                limit=limit,
            )
            return [_node_to_policy(r["p"]) for r in result]

    def link_commit_violates_policy(self, policy_id: str, commit_sha: str) -> None:
        """Create (Commit)-[:VIOLATES]->(Policy) relationship."""
        with self._get_session() as session:
            session.run(
                queries.POLICY_VIOLATES_COMMIT,
                policy_id=policy_id,
                commit_sha=commit_sha,
            )

    def link_reasoning_validated_against_policy(self, reasoning_id: str, policy_id: str) -> None:
        """Create (ReasoningNode)-[:VALIDATED_AGAINST]->(Policy) relationship."""
        with self._get_session() as session:
            session.run(
                queries.REASONING_VALIDATED_AGAINST_POLICY,
                reasoning_id=reasoning_id,
                policy_id=policy_id,
            )

    def get_policy_violations(self, policy_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get all commits that violate a policy."""
        with self._get_session() as session:
            result = session.run(
                queries.GET_POLICY_VIOLATIONS,
                policy_id=policy_id,
                limit=limit,
            )
            return [{"commit": dict(r["c"]), "policy": dict(r["p"])} for r in result]