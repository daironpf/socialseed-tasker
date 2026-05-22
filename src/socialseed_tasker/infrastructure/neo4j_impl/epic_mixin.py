from __future__ import annotations

from datetime import datetime, timezone

from socialseed_tasker.infrastructure import neo4j_queries


class EpicRepositoryMixin:
    """Epic and Objective CRUD operations."""

    def create_epic(self, epic) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.CREATE_EPIC,
                id=str(epic.id),
                name=epic.name,
                description=epic.description,
                objective_id=str(epic.objective_id) if epic.objective_id else None,
                status=epic.status.value,
                createdAt=epic.createdAt.isoformat(),
                updatedAt=epic.updatedAt.isoformat(),
            )

    def get_epic(self, epicId: str):
        from uuid import UUID

        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_EPIC, id=epicId)
            record = result.single()
            if record is None:
                return None
            node = record["e"]
            from socialseed_tasker.domain.entities import Epic, EpicStatus

            return Epic(
                id=UUID(node["id"]),
                name=node["name"],
                description=node.get("description", ""),
                objective_id=UUID(node["objective_id"]) if node.get("objective_id") else None,
                status=EpicStatus(node.get("status", "OPEN")),
            )

    def list_epics(self):
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.LIST_EPICS)
            from uuid import UUID

            from socialseed_tasker.domain.entities import Epic, EpicStatus

            epics = []
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
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_EPIC, id=epicId)

    def link_issue_to_epic(self, issue_id: str, epicId: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.LINK_ISSUE_TO_EPIC, issue_id=issue_id, epicId=epicId)

    def update_epic(self, epicId: str, updates: dict) -> None:
        from datetime import datetime, timezone

        with self._driver.driver.session(database=self._driver.database) as session:
            set_clauses = []
            params = {"id": epicId, "updatedAt": datetime.now(timezone.utc).isoformat()}

            for key, value in updates.items():
                set_clauses.append(f"e.{key} = ${key}")
                params[key] = value

            query = f"MATCH (e:Epic {{id: $id}}) SET {', '.join(set_clauses)} RETURN e"
            session.run(query, **params)

    def create_objective(self, objective) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                queries.CREATE_OBJECTIVE,
                id=str(objective.id),
                name=objective.name,
                description=objective.description,
                status=objective.status.value,
                quarter=objective.quarter,
                createdAt=objective.createdAt.isoformat(),
                updatedAt=objective.updatedAt.isoformat(),
            )

    def get_objective(self, objective_id: str):
        from uuid import UUID

        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.GET_OBJECTIVE, id=objective_id)
            record = result.single()
            if record is None:
                return None
            node = record["o"]
            from socialseed_tasker.domain.entities import Objective, ObjectiveStatus

            return Objective(
                id=UUID(node["id"]),
                name=node["name"],
                description=node.get("description", ""),
                status=ObjectiveStatus(node.get("status", "OPEN")),
                quarter=node.get("quarter", ""),
            )

    def list_objectives(self):
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(queries.LIST_OBJECTIVES)
            from uuid import UUID

            from socialseed_tasker.domain.entities import Objective, ObjectiveStatus

            objectives = []
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
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.DELETE_OBJECTIVE, id=objective_id)

    def link_epic_to_objective(self, epicId: str, objective_id: str) -> None:
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(queries.LINK_EPIC_TO_OBJECTIVE, epicId=epicId, objective_id=objective_id)

    def update_objective(self, objective_id: str, updates: dict) -> None:
        from datetime import datetime, timezone

        with self._driver.driver.session(database=self._driver.database) as session:
            set_clauses = []
            params = {"id": objective_id, "updatedAt": datetime.now(timezone.utc).isoformat()}

            for key, value in updates.items():
                set_clauses.append(f"o.{key} = ${key}")
                params[key] = value

            query = f"MATCH (o:Objective {{id: $id}}) SET {', '.join(set_clauses)} RETURN o"
            session.run(query, **params)
