# Issue #267: Create Repository Implementation Templates

## Description

Create reusable code templates (boilerplate) that developers can copy-paste to quickly implement new repositories following Tasker's patterns. This accelerates development and ensures consistency.

### Current State

When implementing a new repository, developers must:
1. Find an existing similar repository
2. Copy it
3. Modify it to match the new entity

This process is error-prone and time-consuming. A template would speed it up significantly.

### Requirements

#### Create `src/socialseed_tasker/storage/graph_database/templates/`

Create a directory with template files:

```
src/socialseed_tasker/storage/graph_database/templates/
├── base_repository.py.template
├── simple_crud_repository.py.template
├── relationship_repository.py.template
└── queries.py.template
```

#### Template 1: `simple_crud_repository.py.template`

```python
"""{{ entity_name }} Repository - Neo4j storage for {{ entity_description }}.

This template provides basic CRUD operations. Copy to new file and customize.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

# Import your entity from core/
# from socialseed_tasker.core.{{ module }}.entities import {{ EntityName }}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# =============================================================================
# Cypher Queries - Add to storage/graph_database/queries.py
# =============================================================================

# CREATE_{{ ENTITY_NAME_UPPER }} = """
# CREATE (n:{{ EntityName }} {
#     id: $id,
#     name: $name,
#     createdAt: $created_at,
#     updatedAt: $updated_at
# })
# RETURN n
# """

# GET_{{ ENTITY_NAME_UPPER }} = """
# MATCH (n:{{ EntityName }} {id: $id})
# RETURN n
# """

# LIST_{{ ENTITY_NAME_UPPER }}S = """
# MATCH (n:{{ EntityName }})
# RETURN n
# ORDER BY n.name
# LIMIT $limit
# """

# UPDATE_{{ ENTITY_NAME_UPPER }} = """
# MATCH (n:{{ EntityName }} {id: $id})
# SET n += $updates, n.updatedAt = $updated_at
# RETURN n
# """

# DELETE_{{ ENTITY_NAME_UPPER }} = """
# MATCH (n:{{ EntityName }} {id: $id})
# DETACH DELETE n
# """


class {{ EntityName }}Repository:
    """Repository for {{ entity_description }} in Neo4j.
    
    Copy this class to a new file (e.g., user_repository.py) and customize.
    """

    def __init__(self, driver: Any) -> None:
        self._driver = driver

    def create(self, entity: Any) -> None:
        """Create a new {{ entity_name }} in Neo4j."""
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                # queries.CREATE_{{ ENTITY_NAME_UPPER }},
                {
                    "id": str(entity.id),
                    "name": entity.name,
                    "created_at": entity.created_at.isoformat(),
                    "updated_at": entity.updated_at.isoformat(),
                }
            )

    def get(self, entity_id: str) -> Any | None:
        """Get a {{ entity_name }} by ID."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                # queries.GET_{{ ENTITY_NAME_UPPER }},
                {"id": entity_id}
            )
            record = result.single()
            if record is None:
                return None
            # return _node_to_entity(record["n"])
            return dict(record["n"])

    def list(self, limit: int = 50) -> list[Any]:
        """List all {{ entity_name }}s."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                # queries.LIST_{{ ENTITY_NAME_UPPER }}S,
                {"limit": limit}
            )
            # return [_node_to_entity(r["n"]) for r in result]
            return [dict(r["n"]) for r in result]

    def update(self, entity_id: str, updates: dict[str, Any]) -> Any:
        """Update a {{ entity_name }}."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                # queries.UPDATE_{{ ENTITY_NAME_UPPER }},
                {
                    "id": entity_id,
                    "updates": updates,
                    "updated_at": _now_iso(),
                }
            )
            record = result.single()
            if record is None:
                raise ValueError(f"{{ entity_name }} {entity_id} not found")
            # return _node_to_entity(record["n"])
            return dict(record["n"])

    def delete(self, entity_id: str) -> None:
        """Delete a {{ entity_name }}."""
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                # queries.DELETE_{{ ENTITY_NAME_UPPER }},
                {"id": entity_id}
            )

    # -------------------------------------------------------------------------
    # Additional methods for this entity
    # -------------------------------------------------------------------------

    def find_by_name(self, name: str) -> Any | None:
        """Find {{ entity_name }} by exact name."""
        with self._driver.driver.session(database=self._driver.database) as session:
            result = session.run(
                "MATCH (n:{{ EntityName }} {name: $name}) RETURN n",
                {"name": name}
            )
            record = result.single()
            if record is None:
                return None
            return dict(record["n"])


# =============================================================================
# Helper function to convert Neo4j node to domain entity
# =============================================================================

def _node_to_entity(node: dict[str, Any]) -> Any:
    """Convert Neo4j node to domain entity.
    
    Customize this for your entity's properties.
    """
    # Example:
    # from socialseed_tasker.core.{{ module }}.entities import {{ EntityName }}
    # return {{ EntityName }}(
    #     id=UUID(node["id"]),
    #     name=node["name"],
    #     created_at=datetime.fromisoformat(node["createdAt"]),
    #     # ... other fields
    # )
    return node
```

#### Template 2: `relationship_repository.py.template`

```python
"""Relationship Repository Template.

Use this for nodes that primarily manage relationships between other nodes.
Example: Policy links, Agent specializations, etc.
"""

class RelationshipRepository:
    """Template for relationship-focused repositories."""

    def __init__(self, driver: Any) -> None:
        self._driver = driver

    def create_relationship(
        self,
        source_label: str,
        source_id: str,
        target_label: str,
        target_id: str,
        relationship_type: str,
        properties: dict | None = None,
    ) -> None:
        """Create a generic relationship between two nodes."""
        with self._driver.driver.session(database=self._driver.database) as session:
            props = ", " + ", ".join([f"r.{k} = ${k}" for k in (properties or {})]) if properties else ""
            query = f"""
            MATCH (s:{source_label} {{id: $source_id}})
            MATCH (t:{target_label} {{id: $target_id}})
            MERGE (s)-[r:{relationship_type}{props}]->(t)
            """
            params = {"source_id": source_id, "target_id": target_id}
            if properties:
                params.update(properties)
            session.run(query, params)

    def delete_relationship(
        self,
        source_label: str,
        source_id: str,
        target_label: str,
        target_id: str,
        relationship_type: str,
    ) -> None:
        """Delete a relationship between two nodes."""
        with self._driver.driver.session(database=self._driver.database) as session:
            session.run(
                f"""
                MATCH (s:{source_label} {{id: $source_id}})-[r:{relationship_type}]->(t:{target_label} {{id: $target_id}})
                DELETE r
                """,
                {"source_id": source_id, "target_id": target_id},
            )

    def get_related(
        self,
        source_label: str,
        source_id: str,
        relationship_type: str,
        target_label: str | None = None,
    ) -> list[dict]:
        """Get all nodes related to a source via a relationship."""
        with self._driver.driver.session(database=self._driver.database) as session:
            target = f":{target_label}" if target_label else ""
            result = session.run(
                f"""
                MATCH (s:{source_label} {{id: $source_id}})-[r:{relationship_type}]->(t{target})
                RETURN t
                """,
                {"source_id": source_id},
            )
            return [dict(r["t"]) for r in result]
```

#### Template 3: `queries.py.template`

```python
"""Query Template for {{ entity_name }}.

Copy these queries to storage/graph_database/queries.py
and customize the entity name and properties.
"""

# =============================================================================
# Entity Queries
# =============================================================================

CREATE_{{ ENTITY_NAME_UPPER }} = """
CREATE (n:{{ EntityName }} {
    id: $id{% for prop in properties %},
    {{ prop.name }}: ${{ prop.name }}{% endfor %}
})
RETURN n
"""

GET_{{ ENTITY_NAME_UPPER }} = """
MATCH (n:{{ EntityName }} {id: $id})
RETURN n
"""

UPDATE_{{ ENTITY_NAME_UPPER }} = """
MATCH (n:{{ EntityName }} {id: $id})
SET n += $updates, n.updatedAt = $updated_at
RETURN n
"""

DELETE_{{ ENTITY_NAME_UPPER }} = """
MATCH (n:{{ EntityName }} {id: $id})
DETACH DELETE n
"""

LIST_{{ ENTITY_NAME_UPPER }}S = """
MATCH (n:{{ EntityName }})
{% if filters %}
WHERE {% for f in filters %}n.{{ f }} = ${{ f }} {% if not loop.last %}AND {% endif %}{% endfor %}
{% endif %}
RETURN n
ORDER BY n.{{ order_by or 'createdAt' }}
SKIP $skip
LIMIT $limit
"""

# =============================================================================
# Relationship Queries
# =============================================================================

LINK_{{ ENTITY_NAME_UPPER }}_TO_{{ RELATED_ENTITY }} = """
MATCH (n:{{ EntityName }} {id: $id})
MATCH (r:{{ RelatedEntity }} {id: $related_id})
MERGE (n)-[:{{ relationship_name }}]->(r)
RETURN n, r
"""

GET_{{ ENTITY_NAME_UPPER }}_{{ RELATED_ENTITY }}S = """
MATCH (n:{{ EntityName }} {id: $id})-[r:{{ relationship_name }}]->(r:{{ RelatedEntity }})
RETURN r
"""
```

### Add Scripts to Generate Templates

Add a CLI command in `entrypoints/terminal_cli/commands.py`:

```bash
# Generate a new repository from template
tasker generate repository User

# Generate with options
tasker generate repository User --module user_management --relationships
```

### Business Value

1. **Faster development** - Copy-paste instead of starting from scratch
2. **Consistency** - All repositories follow the same pattern
3. **Fewer bugs** - Templates are pre-tested
4. **Onboarding** - New developers can implement features quickly

## Status: PENDING

## Priority: MEDIUM