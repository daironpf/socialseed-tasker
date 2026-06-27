# Issue #247: Align Neo4j Project Schema with v1.0 Documentation

## Description

Update the Neo4j persistence layer to support the full `Project` node schema defined in the v1.0 specification. The current implementation in `Neo4jTaskRepository` only handles a subset of properties (`name`, `description`, `settings`).

### Requirements

1.  **Update Queries**:
    - Modify `CREATE_PROJECT` in `queries.py` to include all 18 properties defined in the documentation.
    - Standardize property names in Cypher to **camelCase** (e.g., `p.mainStack` instead of `p.main_stack` if any existed).
    - Ensure `MERGE` logic uses a unique identifier (like `slug` or `id`) instead of just `name`.

2.  **Update Repository**:
    - Update `Neo4jTaskRepository.create_project_node` to accept the new `Project` domain entity.
    - Update `_node_to_project` (or create it) to correctly map Neo4j properties back to the Pydantic model.
    - Update `list_project_nodes` to return the complete set of properties.

3.  **Schema Constraints**:
    - Add constraints for `Project.id` and `Project.slug` in `SCHEMA_CONSTRAINTS` within `queries.py`.

### Business Value

Ensures that the architectural context and governance rules defined at the project level are persistent and queryable. This enables advanced Cypher queries for cross-project analysis and global governance enforcement.

## Status: COMPLETED
