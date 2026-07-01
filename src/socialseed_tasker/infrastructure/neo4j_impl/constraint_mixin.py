from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from socialseed_tasker.application.constraints import (
    Constraint,
    ConstraintCategory,
    ConstraintLevel,
    ConstraintStatus,
)
from socialseed_tasker.infrastructure.neo4j_impl.shared import _session


class ConstraintRepositoryMixin:
    """Constraint CRUD operations."""

    def create_constraint(self, constraint: Constraint) -> None:
        """Persist a new constraint to Neo4j."""
        with _session(self._driver) as session:
            session.run(
                """
                CREATE (c:Constraint {
                    id: $id,
                    category: $category,
                    level: $level,
                    pattern: $pattern,
                    service: $service,
                    target: $target,
                    from_layer: $from_layer,
                    to_layer: $to_layer,
                    rule_type: $rule_type,
                    max_depth: $max_depth,
                    required: $required,
                    description: $description,
                    status: $status,
                    createdAt: $createdAt,
                    updatedAt: $updatedAt
                })
                """,
                id=str(constraint.id),
                category=constraint.category.value,
                level=constraint.level.value,
                pattern=constraint.pattern,
                service=constraint.service,
                target=constraint.target,
                from_layer=constraint.from_layer,
                to_layer=constraint.to_layer,
                rule_type=constraint.rule_type,
                max_depth=constraint.max_depth,
                required=constraint.required,
                description=constraint.description,
                status=constraint.status.value,
                createdAt=constraint.created_at.isoformat(),
                updatedAt=constraint.updated_at.isoformat(),
            )

    def list_constraints(self, category: str | None = None) -> list[Constraint]:
        """List constraints from Neo4j, optionally filtered by category."""
        with _session(self._driver) as session:
            labels_result = session.run("CALL db.labels()")
            labels = [r["label"] for r in labels_result]
            if "Constraint" not in labels:
                return []

            if category:
                result = session.run(
                    "MATCH (c:Constraint {category: $category}) RETURN c",
                    category=category,
                )
            else:
                result = session.run("MATCH (c:Constraint) RETURN c")

            constraints = []
            for r in result:
                node = dict(r["c"])
                constraints.append(
                    Constraint(
                        id=node.get("id"),
                        category=ConstraintCategory(node.get("category", "architecture")),
                        level=ConstraintLevel(node.get("level", "hard")),
                        pattern=node.get("pattern", ""),
                        service=node.get("service", ""),
                        target=node.get("target", ""),
                        from_layer=node.get("from_layer", ""),
                        to_layer=node.get("to_layer", ""),
                        rule_type=node.get("rule_type", ""),
                        max_depth=node.get("max_depth"),
                        required=node.get("required", True),
                        description=node.get("description", ""),
                        status=ConstraintStatus(node.get("status", "inactive")),
                    )
                )
            return constraints

    def get_constraint(self, constraint_id: str) -> Constraint | None:
        """Retrieve a constraint by ID."""
        with _session(self._driver) as session:
            result = session.run(
                "MATCH (c:Constraint {id: $id}) RETURN c",
                id=constraint_id,
            )
            record = result.single()
            if record is None:
                return None

            node = dict(record["c"])
            return Constraint(
                id=node.get("id"),
                category=ConstraintCategory(node.get("category", "architecture")),
                level=ConstraintLevel(node.get("level", "hard")),
                pattern=node.get("pattern", ""),
                service=node.get("service", ""),
                target=node.get("target", ""),
                from_layer=node.get("from_layer", ""),
                to_layer=node.get("to_layer", ""),
                rule_type=node.get("rule_type", ""),
                max_depth=node.get("max_depth"),
                required=node.get("required", True),
                description=node.get("description", ""),
                status=ConstraintStatus(node.get("status", "inactive")),
            )

    def delete_constraint(self, constraint_id: str) -> None:
        """Delete a constraint from Neo4j."""
        with _session(self._driver) as session:
            session.run(
                "MATCH (c:Constraint {id: $id}) DETACH DELETE c",
                id=constraint_id,
            )

    def update_constraint(self, constraint_id: str, updates: dict) -> Constraint:
        """Update a constraint in Neo4j."""
        with _session(self._driver) as session:
            set_clauses = []
            params = {"id": constraint_id}

            for key, value in updates.items():
                set_clauses.append(f"c.{key} = ${key}")
                params[key] = value

            set_clauses.append("c.updatedAt = $updatedAt")
            params["updatedAt"] = datetime.now(timezone.utc).isoformat()

            query = f"MATCH (c:Constraint {{id: $id}}) SET {', '.join(set_clauses)} RETURN c"
            result = session.run(query, **params)
            record = result.single()

            if record is None:
                raise ValueError(f"Constraint {constraint_id} not found")

            return self.get_constraint(constraint_id)
