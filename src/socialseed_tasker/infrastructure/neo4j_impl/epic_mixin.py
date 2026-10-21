from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from socialseed_tasker.domain.entities import Epic, EpicStatus, Objective, ObjectiveStatus
from socialseed_tasker.infrastructure import neo4j_queries as queries
from socialseed_tasker.infrastructure.neo4j_impl.shared import _session

_EPIC_UPDATABLE_FIELDS = frozenset({"name", "description", "objective_id", "status"})
_OBJECTIVE_UPDATABLE_FIELDS = frozenset({"name", "description", "status", "quarter"})


class EpicRepositoryMixin:
    """Epic and Objective CRUD operations."""

    def create_epic(self, epic: Epic) -> None:
        with _session(self._driver) as session:
            session.run(
                queries.CREATE_EPIC,
                id=str(epic.id),
                name=epic.name,
                description=epic.description,
                objective_id=str(epic.objective_id) if epic.objective_id else None,
                status=epic.status.value,
                created_at=epic.created_at.isoformat(),
                updated_at=epic.updated_at.isoformat(),
            )

    def get_epic(self, epicId: str) -> Epic | None:
        with _session(self._driver) as session:
            result = session.run(queries.GET_EPIC, id=epicId)
            record = result.single()
            if record is None:
                return None
            node = record["e"]

            return Epic(
                id=UUID(node["id"]),
                name=node["name"],
                description=node.get("description", ""),
                objective_id=UUID(node["objective_id"]) if node.get("objective_id") else None,
                status=EpicStatus(node.get("status", "OPEN")),
            )

    def list_epics(self) -> list[Epic]:
        with _session(self._driver) as session:
            result = session.run(queries.LIST_EPICS)

            epics: list[Epic] = []
            for record in result:
                node = record["e"]
                epics.append(
                    Epic(
                        id=UUID(node["id"]),
                        name=node["name"],
                        description=node.get("description", ""),
                        objective_id=UUID(node["objective_id"]) if node.get("objective_id") else None,
                        status=EpicStatus(node.get("status", "OPEN")),
                    )
                )
            return epics

    def delete_epic(self, epicId: str) -> None:
        with _session(self._driver) as session:
            session.run(queries.DELETE_EPIC, id=epicId)

    def link_issue_to_epic(self, issue_id: str, epicId: str) -> None:
        with _session(self._driver) as session:
            session.run(queries.LINK_ISSUE_TO_EPIC, issue_id=issue_id, epic_id=epicId)

    def update_epic(self, epicId: str, updates: dict) -> None:
        safe_updates = {k: v for k, v in updates.items() if k in _EPIC_UPDATABLE_FIELDS}
        if not safe_updates:
            return
        with _session(self._driver) as session:
            params = {"id": epicId, "updated_at": datetime.now(timezone.utc).isoformat()}
            set_clauses = ["e.updatedAt = $updated_at"]

            for key, value in safe_updates.items():
                set_clauses.append(f"e.{key} = ${key}")
                params[key] = value

            query = f"MATCH (e:Epic {{id: $id}}) SET {', '.join(set_clauses)} RETURN e"
            session.run(query, **params)

    def create_objective(self, objective: Objective) -> None:
        with _session(self._driver) as session:
            session.run(
                queries.CREATE_OBJECTIVE,
                id=str(objective.id),
                name=objective.name,
                description=objective.description,
                status=objective.status.value,
                quarter=objective.quarter,
                created_at=objective.created_at.isoformat(),
                updated_at=objective.updated_at.isoformat(),
            )

    def get_objective(self, objective_id: str) -> Objective | None:
        with _session(self._driver) as session:
            result = session.run(queries.GET_OBJECTIVE, id=objective_id)
            record = result.single()
            if record is None:
                return None
            node = record["o"]

            return Objective(
                id=UUID(node["id"]),
                name=node["name"],
                description=node.get("description", ""),
                status=ObjectiveStatus(node.get("status", "OPEN")),
                quarter=node.get("quarter", ""),
            )

    def list_objectives(self) -> list[Objective]:
        with _session(self._driver) as session:
            result = session.run(queries.LIST_OBJECTIVES)

            objectives: list[Objective] = []
            for record in result:
                node = record["o"]
                objectives.append(
                    Objective(
                        id=UUID(node["id"]),
                        name=node["name"],
                        description=node.get("description", ""),
                        status=ObjectiveStatus(node.get("status", "OPEN")),
                        quarter=node.get("quarter", ""),
                    )
                )
            return objectives

    def delete_objective(self, objective_id: str) -> None:
        with _session(self._driver) as session:
            session.run(queries.DELETE_OBJECTIVE, id=objective_id)

    def link_epic_to_objective(self, epicId: str, objective_id: str) -> None:
        with _session(self._driver) as session:
            session.run(queries.LINK_EPIC_TO_OBJECTIVE, epic_id=epicId, objective_id=objective_id)

    def update_objective(self, objective_id: str, updates: dict) -> None:
        safe_updates = {k: v for k, v in updates.items() if k in _OBJECTIVE_UPDATABLE_FIELDS}
        if not safe_updates:
            return
        with _session(self._driver) as session:
            params = {"id": objective_id, "updated_at": datetime.now(timezone.utc).isoformat()}
            set_clauses = ["o.updatedAt = $updated_at"]

            for key, value in safe_updates.items():
                set_clauses.append(f"o.{key} = ${key}")
                params[key] = value

            query = f"MATCH (o:Objective {{id: $id}}) SET {', '.join(set_clauses)} RETURN o"
            session.run(query, **params)
