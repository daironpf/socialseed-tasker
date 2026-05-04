# Developer Guide: RAG and Vector Indexes (v0.9.0)

This guide covers the RAG (Retrieval-Augmented Generation) capabilities in SocialSeed Tasker v0.9.0.

## Overview

RAG enables semantic search across your task history, codebase, and documentation using vector embeddings stored in Neo4j.

## Architecture

### Components
1. **Embedding Service**: Generates vector embeddings using OpenAI or local models
2. **RAG Repository**: Stores and retrieves embeddings from Neo4j
3. **Vector Index**: Neo4j native vector index for similarity search

### Flow
```
User Query → Embedding Service → Vector Search in Neo4j → Results
```

## Setup

### 1. Configure Environment
```bash
# Set OpenAI API key (optional - falls back to simple embeddings)
export OPENAI_API_KEY="sk-..."
```

### 2. Run Migration
```bash
tasker storage migrate --version 0.9.0
```

This creates the vector index:
```cypher
CREATE VECTOR INDEX rag_index IF NOT EXISTS 
FOR (e:RAGEmbedding) ON e.embedding
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}
```

## Usage

### CLI Commands

#### Semantic Search
```bash
# Search for similar solutions
tasker rag search "how to implement JWT authentication"
```

#### Index Issues
```bash
# Index an issue for search
tasker rag index --source issue --id <issue-id>
```

#### View Stats
```bash
tasker rag stats
```

### API Endpoints

#### Search
```bash
curl "http://localhost:8000/api/v1/rag/search?q=authentication+flow&limit=5"
```

Response:
```json
{
  "results": [
    {
      "id": "uuid",
      "content": "Implemented JWT authentication using...",
      "source_type": "issue",
      "source_id": "uuid",
      "score": 0.92
    }
  ]
}
```

#### Index Content
```bash
curl -X POST "http://localhost:8000/api/v1/rag/index" \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "issue",
    "source_id": "uuid",
    "content": "Issue content to index"
  }'
```

## Embedding Strategies

### Chunking Strategies

The RAG system supports different text chunking strategies:

| Strategy | Description | Best For |
|----------|-------------|----------|
| `paragraph` | Split by paragraphs | Long documents |
| `lines` | Split by lines | Code, logs |
| `sentences` | Split by sentences | Natural language |

### Using Different Strategies

```python
from socialseed_tasker.storage.graph_database.rag_repository import RAGRepository

repo.index_text(
    text="Long document content...",
    source_type="issue",
    source_id="uuid",
    chunking_strategy="paragraph"  # or "lines" or "sentences"
)
```

## Integration with Agents

### Get Context for Agent

```bash
tasker agent context --issue <issue-id>
```

This command:
1. Finds similar past issues using RAG
2. Retrieves relevant code symbols
3. Gets dependency context
4. Returns comprehensive context for the agent

### Similar Issues

```bash
tasker agent suggest --issue <issue-id>
```

## Vector Index Configuration

### Dimensions
- Default: 1536 (OpenAI ada-002)
- Configurable via `vector.dimensions` in index creation

### Similarity Function
- Default: `cosine` (recommended for semantic search)
- Alternative: `euclidean` or `dot-product`

### Query Example
```cypher
CALL db.index.vector.searchNodes('rag_index', 5, $embedding)
YIELD node, score
RETURN node.content, score
ORDER BY score DESC
```

## Fallback Search

If vector indexes are unavailable, the system falls back to computing cosine similarity in Python:

```python
def cosine_similarity(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * y for y in b))
    return dot / (mag_a * mag_b)
```

## Troubleshooting

### Vector Index Not Found
If you see "Vector index not found", run migration:
```bash
tasker storage migrate --version 0.9.0
```

### Embedding Service Unavailable
The system automatically falls back to text-only search without embeddings.

### Performance Issues
- Ensure Neo4j Aura or adequate hardware for vector operations
- Consider batch indexing for large content

## Best Practices

1. **Index decisions and reasoning** - Helps future agents understand choices
2. **Chunk appropriately** - Balance between context and specificity
3. **Use semantic search for debugging** - Find similar past issues quickly
4. **Combine with Code Graph** - Get both semantic context and code structure

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/rag/search` | Semantic search |
| GET | `/rag/similar-issues` | Find similar issues |
| POST | `/rag/embed` | Generate embedding |
| POST | `/rag/index` | Index content |
| GET | `/rag/stats` | Get RAG statistics |
| DELETE | `/rag/clear` | Clear all embeddings |