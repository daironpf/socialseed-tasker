---
title: "RAG Context Window Manager (Token Pruning)"
component: "RAG Intelligence"
priority: "MEDIUM"
status: "DONE"
version: "v1.0.0"
---

# Issue #232: RAG Context Window Manager (Token Pruning)

## Description
Limit RAG response size to prevent token overflow.

## Acceptance Criteria
- [x] Add max_content_size parameter to RAG search.
- [x] Truncate oversized content.

## Status: DONE

## Resolution (2026-05-04)
- [x] Add max_content_size query param to /rag/search
- [x] Truncate content exceeding limit
- [x] Return content_length for reference

### Usage
```bash
curl -X POST "http://localhost:8000/api/v1/rag/search?query=test&max_content_size=4000"
```
