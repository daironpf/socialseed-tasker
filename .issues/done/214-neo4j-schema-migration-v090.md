# Issue #214: Neo4j Schema Migration for v0.9.0

## Description

Create Neo4j schema migration for v0.9.0 features: vector indexes, Code-as-Graph nodes, and Reasoning nodes.

## Problem

New features require schema changes in Neo4j:
- Vector indexes for RAG
- New node types for Code-as-Graph
- New relationship types for Reasoning

## Required Schema Changes

### Vector Indexes (for RAG)
```cypher
// Create vector index for issue embeddings
CREATE VECTOR INDEX issue_embeddings IF NOT EXISTS
FOR (i:Issue) ON (i.embedding)
OPTIONS {dimension: 1536, similarityFunction: 'cosine'}
```

### Code-as-Graph Nodes
```cypher
// Add constraints for Code-as-Graph nodes
CREATE CONSTRAINT code_file_id IF NOT EXISTS
FOR (f:CodeFile) REQUIRE f.id IS UNIQUE

CREATE CONSTRAINT code_symbol_id IF NOT EXISTS
FOR (s:CodeSymbol) REQUIRE s.id IS UNIQUE
```

### Reasoning Nodes
```cypher
// Add constraints for Reasoning nodes
CREATE CONSTRAINT reasoning_node_id IF NOT EXISTS
FOR (r:ReasoningNode) REQUIRE r.id IS UNIQUE

CREATE INDEX reasoning_timestamp IF NOT EXISTS
FOR (r:ReasoningNode) ON (r.timestamp)
```

### New Relationship Types
```cypher
// Code-as-Graph relationships
CREATE INDEX code_calls IF NOT EXISTS
FOR ()-[r:CALLS]->() ON (r.timestamp)

CREATE INDEX code_depends IF NOT EXISTS
FOR ()-[r:DEPENDS_ON]->() ON (r.timestamp)

// Reasoning relationships
CREATE INDEX agent_thought IF NOT EXISTS
FOR ()-[r:THOUGHT]->() ON (r.timestamp)
```

## Migration Strategy

1. **Check existing constraints/indexes**
2. **Add new constraints**
3. **Add new indexes**
4. **Verify migration success**
5. **Rollback capability**

## Status

**COMPLETED**

## Priority

**HIGH** - Required for v0.9.0

## Component

STORAGE

## Acceptance Criteria

- [x] Create migration script
- [x] Add vector index for RAG
- [x] Add constraints for Code-as-Graph
- [x] Add constraints for Reasoning
- [x] Add indexes for performance
- [x] Add rollback capability
- [x] Document schema changes
- [x] Test migration on fresh database
- [x] Test migration on existing database