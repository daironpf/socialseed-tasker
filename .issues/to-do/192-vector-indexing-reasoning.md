# Issue #192 - Vector Indexing for Reasoning Logs

## Description

Add vector search capability to Neo4j for semantic search over Issue descriptions and reasoning logs, enabling AI agents to find relevant context.

## Problem

`reasoning_logs` are stored but not searchable by similarity. AI agents need semantic search to find similar issues and reasoning patterns.

## Acceptance Criteria

- [ ] Enable Neo4j vector index on:
  - Issue.description
  - Issue.reasoning_logs (concatenated text)
- [ ] Add endpoint: `GET /ai/search-context?q=...` for semantic search
- [ ] Add endpoint: `GET /ai/similar-issues/{id}` to find similar issues
- [ ] Use embedding model (OpenAI ada-002 or similar)
- [ ] Store vectors in Neo4j property

## Technical Notes

Neo4j vector index creation (requires Neo4j Aura or self-hosted with vector plugin):
```cypher
CREATE VECTOR INDEX issue_descriptions FOR (i:Issue) ON (i.description_embedding)
OPTIONS {vectorDim: 1536, vectorAlg: 'cosine'}
```

Embedding generation:
```python
# Use OpenAI ada-002 or similar
def generate_embedding(text: str) -> list[float]:
    response = openai_client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding
```

Semantic search query:
```cypher
CALL db.index.vector.query('issue_descriptions', 5, $embedding)
YIELD node, score
RETURN node.title, score
```

## API Impact

| Endpoint | Method | Description |
|----------|--------|--------------|
| `/api/v1/ai/search-context` | GET | Semantic search (q=) |
| `/api/v1/ai/similar-issues/{id}` | GET | Find similar issues |
| `/api/v1/issues/{id}/embed` | POST | Generate/regenerate embedding |

## Business Value

- "Find issues similar to this one"
- AI agent context retrieval
- Root cause pattern discovery

## Priority

MEDIUM - Requires Neo4j Aura or vector plugin