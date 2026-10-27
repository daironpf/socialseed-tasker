from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from socialseed_tasker.domain.entities import Component
from socialseed_tasker.infrastructure import neo4j_queries as queries
from socialseed_tasker.infrastructure.neo4j_impl.shared import (
    _Neo4jMixin,
    _node_to_component,
    _now_iso,
    _session,
    _to_camel,
)


class ComponentRepositoryMixin(_Neo4jMixin):
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
                    projectId: $project_id,
                    createdAt: $created_at,
                    updatedAt: $updated_at
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
                project_id=str(component.project_id) if component.project_id else None,
                created_at=component.created_at.isoformat(),
                updated_at=component.updated_at.isoformat(),
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

    def list_project_nodes(self) -> list[dict[Any, Any]]:
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
            "slug": project_data.get("slug")
            or project_data["name"].strip().lower().replace(" ", "-"),
            "description": project_data.get("description", ""),
            "repository_url": project_data.get("repositoryUrl"),
            "base_package": project_data.get("basePackage"),
            "visibility": project_data.get("visibility", "PUBLIC"),
            "status": project_data.get("status", "DEVELOPMENT"),
            "tech_stack": project_data.get("techStack", []),
            "main_stack": project_data.get("mainStack", []),
            "architecture_style": project_data.get("architectureStyle", "api-first"),
            "version": project_data.get("version", "0.1.0"),
            "conventions_url": project_data.get("conventionsUrl"),
            "conventions_rules": project_data.get("conventionsRules"),
            "last_full_scan": now,
            "global_status": project_data.get("globalStatus", "DEVELOPMENT"),
            "created_at": now,
            "updated_at": now,
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
        repository_url: str | None = None,
        base_package: str | None = None,
        visibility: str = "PRIVATE",
        status: str = "ACTIVE",
        tech_stack: list[Any] | None = None,
        main_stack: list[Any] | None = None,
        architecture_style: str | None = None,
        version: str = "0.0.1",
        conventions_url: str | None = None,
        conventions_rules: str | None = None,
        last_full_scan: str | None = None,
        global_status: str = "DEVELOPMENT",
    ) -> dict[Any, Any]:
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc).isoformat()
        params = {
            "id": id,
            "name": name,
            "slug": slug,
            "description": description,
            "repository_url": repository_url,
            "base_package": base_package,
            "visibility": visibility,
            "status": status,
            "tech_stack": tech_stack or [],
            "main_stack": main_stack or [],
            "architecture_style": architecture_style,
            "version": version,
            "conventions_url": conventions_url,
            "conventions_rules": conventions_rules,
            "last_full_scan": last_full_scan,
            "global_status": global_status,
            "created_at": now,
            "updated_at": now,
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
            raise RuntimeError("Neo4j did not return the created project")

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

    def update_component(self, component_id: str, updates: dict[str, Any]) -> Component:
        with _session(self._driver) as session:
            camel_updates = {_to_camel(k): v for k, v in updates.items()}
            result = session.run(
                queries.UPDATE_COMPONENT,
                id=component_id,
                updates=camel_updates,
                updated_at=_now_iso(),
            )
            record = result.single()
            if record is None:
                raise ValueError(f"Component {component_id} not found")
            return _node_to_component(record["c"])

    def delete_component(self, component_id: str) -> None:
        with _session(self._driver) as session:
            session.run(queries.DELETE_COMPONENT, id=component_id)

    def add_component_dependency(self, component_id: str, depends_on_id: str) -> None:
        with _session(self._driver) as session:
            session.run(
                queries.ADD_COMPONENT_DEPENDENCY,
                component_id=component_id,
                depends_on_id=depends_on_id,
            )

    def remove_component_dependency(self, component_id: str, depends_on_id: str) -> None:
        with _session(self._driver) as session:
            session.run(
                queries.REMOVE_COMPONENT_DEPENDENCY,
                component_id=component_id,
                depends_on_id=depends_on_id,
            )

    def get_component_dependencies(self, component_id: str) -> list[Component]:
        with _session(self._driver) as session:
            result = session.run(
                queries.GET_COMPONENT_DEPENDENCIES,
                component_id=component_id,
            )
            return [_node_to_component(r["dep"]) for r in result]

    def get_component_dependents(self, component_id: str) -> list[Component]:
        with _session(self._driver) as session:
            result = session.run(
                queries.GET_COMPONENT_DEPENDENTS,
                component_id=component_id,
            )
            return [_node_to_component(r["dependent"]) for r in result]
