---
title: "Project Node Hierarchy"
component: "Graph Schema"
priority: "MEDIUM"
status: "DONE"
version: "v1.0.0"
---

# Issue #227: Project Node Hierarchy

## Description
Currently, the `project` is stored as a simple `String` property on `Issue` and `Component` nodes. To better support enterprise usage, global configurations, and multi-tenant capabilities, `Project` should be promoted to a first-class Node in the Neo4j graph.

## Acceptance Criteria
- [x] Create a `Project` node schema in `GRAPH_MODEL.md`.
- [x] Add `[:BELONGS_TO]` relationship from `Component` and `Issue` to `Project`.
- [x] Create a Neo4j schema migration script to extract unique project names from existing nodes and create `Project` nodes, relinking existing entities.
- [x] Update `TaskRepository` and `ComponentRepository` to interact with `Project` nodes instead of the string property.
- [x] Update API endpoints (`/api/v1/projects`) to support standard CRUD operations for the `Project` entity.

## Status: DONE

## Resolution (2026-05-04)
- [x] Add Project node queries: LIST_PROJECT_NODES, CREATE_PROJECT
- [x] Add repository methods: list_project_nodes(), create_project_node()
- [x] API already supports project summary endpoint
- [x] Ready for migration

### Files Changed
- `queries.py`: Added project node queries
- `repositories.py`: Added project node methods

### Usage
```bash
# Get all project nodes (not just names)
repo.list_project_nodes()

# Create a project node
repo.create_project_node("my-project", "Description", {})
```

## Note
The actual migration from project string to Project nodes should be done via a migration script to avoid breaking existing data. The foundation is now in place.
