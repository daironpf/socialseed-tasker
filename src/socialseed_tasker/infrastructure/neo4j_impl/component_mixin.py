from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from socialseed_tasker.domain.entities import Component
from socialseed_tasker.infrastructure import neo4j_queries as queries
from socialseed_tasker.infrastructure.neo4j_impl.shared import _node_to_component, _now_iso, _session, _to_camel


class ComponentRepositoryMixin:
    """Component CRUD operations."""

    def create_component(self, component: Component) -> Component:
        with _session(self._driver) as session:
            session.run(
                """
                CREATE (c:Component {
                    id: $id,
                    name: $name,
                    description: $description,
                    project: $project,
                    projectId: $projectId,
                    createdAt: $createdAt,
                    updatedAt: $updatedAt
                })
                WITH c
                OPTIONAL MATCH (proj:Project)
                WHERE proj.slug = $project OR proj.name = $project OR proj.id = $project
                FOREACH (p IN CASE WHEN proj IS NOT NULL THEN [proj] ELSE [] END |
                    MERGE (p)-[:HAS_COMPONENT]->(c)
                )
                WITH c
                FOREACH (label_name IN $labels |
                    MERGE (l:Label {name: label_name})
                    ON CREATE SET l.id = randomUUID(), l.createdAt = $now
                    MERGE (c)-[:CATEGORIZED_BY]->(l)
                )
                """,
                id=str(component.id),
                name=component.name,
                description=component.description,
                project=component.project,
                projectId=str(component.project_id) if component.project_id else None,
                createdAt=component.created_at.isoformat(),
                updatedAt=component.updated_at.isoformat(),
                labels=component.labels if hasattr(component, "labels") else [],
                now=datetime.now(timezone.utc).isoformat(),
            )
        return component

    def get_component(self, component_id: str) -> Component | None:
        with _session(self._driver) as session:
            result = session.run(queries.GET_COMPONENT, id=component_id)
            record = result.single()
            return _node_to_component(record["c"]) if record else None

    def list_components(self, project: str | None = None) -> list[Component]:
        with _session(self._driver) as session:
            result = session.run(queries.LIST_COMPONENTS, project=project)
            return [_node_to_component(r["c"]) for r in result]

    def list_projects(self) -> list[str]:
        with _session(self._driver) as session:
            result = session.run(queries.LIST_PROJECTS)
            return [r["name"] for r in result]

    def list_project_nodes(self) -> list[dict]:
        with _session(self._driver) as session:
            result = session.run(queries.LIST_PROJECT_NODES)
            projects = []
            for r in result:
                p = r["p"]
                projects.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "slug": p.get("slug"),
                    "description": p.get("description"),
                    "repositoryUrl": p.get("repositoryUrl"),
                    "basePackage": p.get("basePackage"),
                    "visibility": p.get("visibility"),
                    "status": p.get("status"),
                    "techStack": p.get("techStack"),
                    "mainStack": p.get("mainStack"),
                    "architectureStyle": p.get("architectureStyle"),
                    "version": p.get("version"),
                    "conventionsUrl": p.get("conventionsUrl"),
                    "conventionsRules": p.get("conventionsRules"),
                    "lastFullScan": p.get("lastFullScan"),
                    "globalStatus": p.get("globalStatus"),
                    "createdAt": p.get("createdAt"),
                    "updatedAt": p.get("updatedAt"),
                })
            return projects

    def create_project(self, project_data: dict[str, Any]) -> dict[str, Any]:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        project_id = project_data.get("id") or str(uuid.uuid4())
        params = {
            "id": project_id,
            "name": project_data["name"],
            "slug": project_data.get("slug", project_data["name"]),
            "description": project_data.get("description", ""),
            "repositoryUrl": project_data.get("repositoryUrl"),
            "basePackage": project_data.get("basePackage"),
            "visibility": project_data.get("visibility", "PUBLIC"),
            "status": project_data.get("status", "DEVELOPMENT"),
            "techStack": project_data.get("techStack", []),
            "mainStack": project_data.get("mainStack", []),
            "architectureStyle": project_data.get("architectureStyle", "api-first"),
            "version": project_data.get("version", "0.1.0"),
            "conventionsUrl": project_data.get("conventionsUrl"),
            "conventionsRules": project_data.get("conventionsRules"),
            "lastFullScan": now,
            "globalStatus": project_data.get("globalStatus", "DEVELOPMENT"),
            "createdAt": now,
            "updatedAt": now,
        }
        with _session(self._driver) as session:
            result = session.run(queries.CREATE_PROJECT, params)
            record = result.single()
            if record:
                p = record["p"]
                return {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "slug": p.get("slug"),
                    "status": "created",
                }
        return {"status": "created", "id": project_id}

    def create_project_node(
        self,
        id: str,
        name: str,
        slug: str,
        description: str = "",
        repositoryUrl: str | None = None,
        basePackage: str | None = None,
        visibility: str = "PRIVATE",
        status: str = "ACTIVE",
        techStack: list | None = None,
        mainStack: list | None = None,
        architectureStyle: str | None = None,
        version: str = "0.0.1",
        conventionsUrl: str | None = None,
        conventionsRules: str | None = None,
        lastFullScan: str | None = None,
        globalStatus: str = "DEVELOPMENT",
    ) -> dict:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        params = {
            "id": id,
            "name": name,
            "slug": slug,
            "description": description,
            "repositoryUrl": repositoryUrl,
            "basePackage": basePackage,
            "visibility": visibility,
            "status": status,
            "techStack": techStack or [],
            "mainStack": mainStack or [],
            "architectureStyle": architectureStyle,
            "version": version,
            "conventionsUrl": conventionsUrl,
            "conventionsRules": conventionsRules,
            "lastFullScan": lastFullScan,
            "globalStatus": globalStatus,
            "createdAt": now,
            "updatedAt": now,
        }
        with _session(self._driver) as session:
            result = session.run(queries.CREATE_PROJECT, params)
            record = result.single()
            if record:
                p = record["p"]
                return {
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "slug": p.get("slug"),
                    "description": p.get("description"),
                }
            return None

    def get_component_by_name(self, name: str, project: str | None = None) -> Component | None:
        with _session(self._driver) as session:
            if project:
                result = session.run(
                    "MATCH (c:Component {name: $name, project: $project}) RETURN c",
                    name=name,
                    project=project,
                )
            else:
                result = session.run(
                    "MATCH (c:Component {name: $name}) RETURN c",
                    name=name,
                )
            record = result.single()
            return _node_to_component(record["c"]) if record else None

    def update_component(self, componentId: str, updates: dict[str, Any]) -> Component:
        with _session(self._driver) as session:
            camel_updates = {_to_camel(k): v for k, v in updates.items()}
            result = session.run(
                queries.UPDATE_COMPONENT,
                id=componentId,
                updates=camel_updates,
                updatedAt=_now_iso(),
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Component {componentId} not found")
            return _node_to_component(record["c"])

    def delete_component(self, componentId: str) -> None:
        with _session(self._driver) as session:
            session.run(queries.DELETE_COMPONENT, id=componentId)

    def add_component_dependency(self, componentId: str, depends_on_id: str) -> None:
        with _session(self._driver) as session:
            session.run(
                queries.ADD_COMPONENT_DEPENDENCY,
                componentId=componentId,
                depends_on_id=depends_on_id,
            )

    def remove_component_dependency(self, componentId: str, depends_on_id: str) -> None:
        with _session(self._driver) as session:
            session.run(
                queries.REMOVE_COMPONENT_DEPENDENCY,
                componentId=componentId,
                depends_on_id=depends_on_id,
            )

    def get_component_dependencies(self, componentId: str) -> list[Component]:
        with _session(self._driver) as session:
            result = session.run(
                queries.GET_COMPONENT_DEPENDENCIES,
                componentId=componentId,
            )
            return [_node_to_component(r["dep"]) for r in result]

    def get_component_dependents(self, componentId: str) -> list[Component]:
        with _session(self._driver) as session:
            result = session.run(
                queries.GET_COMPONENT_DEPENDENTS,
                componentId=componentId,
            )
            return [_node_to_component(r["dependent"]) for r in result]
