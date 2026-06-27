# Issue #249: Align Organizational and Governance Nodes (Component, Label)

## Description

Update the `Component` and `Label` entities and their Neo4j representations to align with the v1.0 Data Model. This includes renaming properties to `camelCase` and ensuring the correct relationship structure.

### Required Changes

#### 1. `Component` (n2)
- Update `Component` in `src/socialseed_tasker/core/task_management/entities.py`.
- Ensure properties: `id`, `name`, `description`, `createdAt`.
- **Relationship**: Ensure `(Project)-[:HAS_COMPONENT]->(Component)` is the primary way to link components to projects, replacing or augmenting the current `project: str` field.

#### 2. `Label` (n12)
- Update/Implement `Label` entity.
- Properties: `id`, `name`, `color`, `description`, `createdAt`.
- **Relationship**: Ensure `(Issue)-[:HAS_LABEL]->(Label)` is correctly implemented in the repository.

### Requirements
- Use **camelCase** for all property names in both Pydantic and Neo4j.
- Update `Neo4jTaskRepository` methods: `create_component`, `list_components`, `sync_labels_from_github`.
- Update `queries.py` definitions for `CREATE_COMPONENT` and `CREATE_LABEL`.

### Business Value
Standardizing these nodes allows for consistent filtering and reporting across the entire ecosystem, ensuring that "Labels" and "Components" behave predictably for both humans and agents.

## Status: COMPLETED
