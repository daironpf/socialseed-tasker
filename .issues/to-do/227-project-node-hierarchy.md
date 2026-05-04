---
title: "Project Node Hierarchy"
component: "Graph Schema"
priority: "MEDIUM"
status: "TODO"
version: "v1.0.0"
---

# Issue #227: Project Node Hierarchy

## Description
Currently, the `project` is stored as a simple `String` property on `Issue` and `Component` nodes. To better support enterprise usage, global configurations, and multi-tenant capabilities, `Project` should be promoted to a first-class Node in the Neo4j graph.

## Acceptance Criteria
- [ ] Create a `Project` node schema in `GRAPH_MODEL.md`.
- [ ] Add `[:BELONGS_TO]` relationship from `Component` and `Issue` to `Project`.
- [ ] Create a Neo4j schema migration script to extract unique project names from existing nodes and create `Project` nodes, relinking existing entities.
- [ ] Update `TaskRepository` and `ComponentRepository` to interact with `Project` nodes instead of the string property.
- [ ] Update API endpoints (`/api/v1/projects`) to support standard CRUD operations for the `Project` entity.

## Technical Notes
- Converting `project` to a Node allows us to attach settings, agent configurations, and access control policies directly to the project level.
- Ensure the migration script is idempotent.
