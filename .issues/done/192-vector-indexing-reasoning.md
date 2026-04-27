# Issue #192 - Vector Indexing for Reasoning Logs

## Description

Add vector search capability to Neo4j for semantic search over Issue descriptions and reasoning logs, enabling AI agents to find relevant context.

## Problem

`reasoning_logs` are stored but not searchable by similarity. AI agents need semantic search to find similar issues and reasoning patterns.

## Acceptance Criteria

- [x] Enable Neo4j vector index on:
  - Issue.description_embedding (stored)
- [x] Add endpoint: `GET /ai/search-context?q=...` for semantic search
- [x] Add endpoint: `GET /ai/similar-issues/{id}` to find similar issues
- [x] Use embedding model (OpenAI ada-002)
- [x] Store vectors in Neo4j property

## Technical Notes

Neo4j vector search (requires apoc.algo.similarity):
```cypher
MATCH (i:Issue)
WITH i, apoc.algo.similarity(i.description_embedding, $embedding, 'cosine') AS score
WHERE score > $threshold
RETURN i.title, score
```

Embedding generation:
```python
def generate_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding
```

## API Impact

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/api/v1/ai/search-context` | GET | Semantic search (q=) |
| `/api/v1/ai/similar-issues/{id}` | GET | Find similar issues |
| `/api/v1/ai/issues/{id}/embed` | POST | Generate/regenerate embedding |

## Business Value

- "Find issues similar to this one"
- AI agent context retrieval
- Root cause pattern discovery

## Status

**COMPLETED** - April 26, 2026

### Implementation Summary

- Added `description_embedding` field (list[float]) to Issue entity
- Added Neo4j queries: SEARCH_BY_EMBEDDING, FIND_SIMILAR_ISSUES, UPDATE_ISSUE_EMBEDDING
- Added repository methods: search_by_embedding, find_similar_issues, update_issue_embedding
- Added REST API endpoints:
  - `GET /api/v1/ai/search-context?q=...` - Semantic search using OpenAI ada-002
  - `GET /api/v1/ai/similar-issues/{id}` - Find issues similar to given issue
  - `POST /api/v1/ai/issues/{id}/embed` - Generate/regenerate embedding

**Commit**: bd8e86d