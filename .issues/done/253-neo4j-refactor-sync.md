# Issue #253: Comprehensive Neo4j Repository Refactor for v1.0 Alignment

## Description

This is the final "glue" issue to ensure that the entire storage layer is synchronized with the v1.0 Graph Data Model. It involves a massive cleanup of `queries.py` and all repositories.

### Required Changes

1.  **Schema Normalization**:
    - Update `SCHEMA_CONSTRAINTS` in `queries.py` for all 13 node types.
    - Update `SCHEMA_INDEXES` to use the new `camelCase` property names.

2.  **Repository Synchronization**:
    - Update `code_graph_repository.py` to support the new `CodeFile`, `CodeSymbol`, and `CodeImport` structures.
    - Update `reasoning_repository.py` for the new `ReasoningNode` and `Agent` properties.
    - Update `rag_repository.py` for `RAGEmbedding` context definitions.

3.  **Relationship Enforcement**:
    - Ensure all `MERGE` and `CREATE` operations in Cypher use the standard relationship names (e.g., `[:HAS_COMPONENT]`, `[:DEFINES_CONTEXT]`, `[:VALIDATES]`).

### Requirements
- Eliminate all remaining `snake_case` properties in Neo4j.
- Ensure all repository methods return fully populated Pydantic objects based on the new v1.0 schemas.
- Validate that the Intelligence Queries (Impact Analysis, etc.) from the documentation work correctly with the new schema.

### Business Value
Guarantees that the "Mental Model" of the developer (the documentation) matches the "Physical Reality" of the database. This prevents runtime errors and ensures the system is ready for full AI-native autonomy.

## Status: COMPLETED
