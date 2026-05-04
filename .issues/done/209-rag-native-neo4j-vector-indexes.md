# Issue #209: RAG Native in Graph with Vector Indexes

## Description

Implement vector indexes in Neo4j to enable semantic search across project knowledge, allowing AI agents to find similar past solutions and relevant context.

## Problem

AI agents need to find:
- Similar issues that were solved before
- Past architectural decisions (ADRs)
- Relevant code examples and patterns
- Configuration best practices

Current system only supports exact text search, not semantic similarity.

## Expected Behavior

The system should:
- Store embeddings for tasks and solutions
- Enable similarity matching between queries and stored content
- Support historical solution retrieval
- Inject relevant context into agent prompts

## Technical Implementation

### Vector Indexes in Neo4j
- Use Neo4j vector indexes (available in Neo4j 5.23+)
- Or use external embedding storage with similarity search
- Store vector embeddings for:
  - Issue titles and descriptions
  - Solution summaries
  - Code snippets
  - Documentation chunks

### Embedding Generation Service
- Use OpenAI embeddings (text-embedding-3-small) or local alternatives
- Implement chunking strategies:
  - By file (for code)
  - By paragraph (for docs)
  - By section (for issues)
- Store embedding metadata (source, timestamp, type)

### RAG Pipeline
1. **Query Processing:**
   - Receive user query
   - Generate embedding from query
   - Search vector index for similar results

2. **Context Retrieval:**
   - Retrieve top-K similar items
   - Rank by relevance score
   - Filter by date/recency if needed

3. **Context Injection:**
   - Format retrieved context
   - Inject into prompt
   - Include source citations

### Knowledge Types to Index
- Past issue solutions (closed issues with solution summaries)
- Architectural decisions (ADRs)
- Test patterns and examples
- Configuration best practices
- Code examples from Code-as-Graph

## Steps to Reproduce

```bash
# Not currently implemented - this is the feature to add
tasker rag search "how to fix memory leak in async code"
# Should return similar past issues with solutions

curl -X POST http://localhost:8000/api/v1/rag/search \
  -H "Content-Type: application/json" \
  -d '{"query": "how to fix memory leak in async code", "limit": 5}'
```

## Status

**TODO**

## Priority

**HIGH** - Core feature for v0.9.0

## Component

CORE, STORAGE, API

## Acceptance Criteria

- [ ] Neo4j vector index configuration
- [ ] Embedding generation service
- [ ] Chunking strategies for code/documents/issues
- [ ] Vector similarity search
- [ ] Context injection for agent prompts
- [ ] CLI command: `tasker rag search <query>`
- [ ] API endpoint: `POST /api/v1/rag/search`
- [ ] API endpoint: `POST /api/v1/rag/index`
- [ ] Index issue solutions on close
- [ ] Index ADR documents
- [ ] Security: Filter secrets before embedding
- [ ] Unit tests for RAG pipeline

## Implementation Plan

### Phase 1: Embedding Service
1. Create `embedding_service.py` in `core/services/`
2. Implement OpenAI embedding client
3. Implement chunking strategies
4. Add secret filtering (never embed API keys, passwords)

### Phase 2: Vector Storage
1. Update Neo4j schema for vector storage
2. Create vector index configuration
3. Implement embedding storage queries
4. Implement similarity search queries

### Phase 3: API Integration
1. Add RAG endpoints to API
2. Add CLI commands
3. Implement automatic indexing on issue close
4. Add document indexing commands

### Phase 4: Context Injection
1. Create prompt builder service
2. Format retrieved context
3. Add to agent manifest generation
4. Support source citations

## Security Considerations

- **Critical:** Never store raw API keys/passwords in vector index
- Filter secrets using existing SecretManager
- Use placeholder tokens for sensitive data
- Log embedding requests for audit

## Impact

- AI agents can learn from past solutions
- Reduces重复 work
- Enables knowledge reuse
- Improves agent accuracy

## Related Issues

- #208 - Code-as-Graph with Tree-sitter
- #210 - AI Reasoning Logs in Graph
- #102 - Input Validation (security for RAG)

## Technical Notes

- Neo4j 5.23+ required for native vector indexes
- Alternative: Pinecone, Weaviate, or Qdrant if Neo4j vectors unavailable
- Consider embedding cache for performance
- Monitor token usage for cost control