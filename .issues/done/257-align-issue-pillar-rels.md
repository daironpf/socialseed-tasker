# Issue #257: Align Issue Node and Cross-Pillar Relationships (n5)

## Description

The `Issue` node is the primary driver of work in Tasker. This issue ensures its properties and relationships are fully aligned with the v1.0 specification, enabling high-precision mapping to code and commits.

### Required Changes

#### 1. `Issue` (n5) Properties
- Update `Issue` entity to use **camelCase**.
- Properties: `id`, `title`, `description`, `status`, `priority`, `createdAt`, `updatedAt`, `closedAt`.

#### 2. Cross-Pillar Relationships
- **(Issue)-[:AFFECTS]->(CodeSymbol)**: Links the requirement to the specific classes/methods.
- **(Issue)-[:RESOLVED_BY]->(Commit)**: Links the requirement to the physical code change.
- **(Issue)-[:HAS_LABEL]->(Label)**: Ensures categorization for automated routing.
- **(User/Agent)-[:ASSIGNED_TO]->(Issue)**: Tracks responsibility.

### Requirements
- Update `src/socialseed_tasker/core/task_management/entities.py`.
- Ensure `Neo4jTaskRepository` can handle these relationships during issue creation and resolution.
- Standardize Enums for `status` and `priority`.

### Business Value
This alignment is what enables "Causal Traceability." By linking issues directly to code symbols and commits, the system provides a perfect audit trail of why every line of code exists.

## Status: COMPLETED
