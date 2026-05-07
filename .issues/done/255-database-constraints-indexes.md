# Issue #255: Implement Database Constraints and Vector Search Indexing

## Description

To ensure the integrity of the v1.0 Graph Model, we must implement all constraints and indexes defined in the documentation. This is especially critical for semantic search (RAG).

### Required Constraints & Indexes

#### 1. Unique Constraints
Implement `REQUIRE x.id IS UNIQUE` for:
- `Project`, `Component`, `Agent`, `User`, `Issue`, `CodeFile`, `CodeSymbol`, `CodeImport`, `ReasoningNode`, `RAGEmbedding`, `Label`, `Policy`.

#### 2. Performance Indexes
Implement indexes for:
- `Component(name)`
- `Agent(role)`
- `Issue(status)`
- `CodeFile(path, name)`
- `CodeSymbol(name)`
- `Commit(timestamp)`
- `Label(name)`
- `Policy(name)`

#### 3. Vector Index (CRITICAL)
- `CREATE VECTOR INDEX rag_content_index FOR (re:RAGEmbedding) ON (re.embedding);`

### Requirements
- Update the `SCHEMA_CONSTRAINTS` and `SCHEMA_INDEXES` constants in `src/socialseed_tasker/storage/graph_database/queries.py`.
- Add a migration script or a startup check to ensure these exist in the Neo4j instance.

### Business Value
Constraints prevent data corruption (e.g., duplicate projects), while indexes (especially the vector index) are what make the AI's search and reasoning phases fast and scalable.

## Status: COMPLETED
