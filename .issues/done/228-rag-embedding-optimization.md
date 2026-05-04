---
title: "RAG Embedding Storage Optimization"
component: "RAG Intelligence"
priority: "HIGH"
status: "DONE"
version: "v1.0.0"
---

# Issue #228: RAG Embedding Storage Optimization

## Description
Store RAG embeddings directly on source nodes (Issue, CodeSymbol, ReasoningNode) instead of separate RAGEmbedding nodes for better performance.

## Acceptance Criteria
- [x] Add `embedding` property directly on `Issue`, `CodeSymbol`, `ReasoningNode` via methods.
- [x] Update RAGRepository to store vectors on source nodes.
- [x] Add CLI commands for native embeddings.

## Status: DONE

## Resolution (2026-05-04)
- [x] Add create_native_embedding() method
- [x] Add search_native() method
- [x] CLI: tasker rag embed-native
- [x] CLI: tasker rag search-native
- [x] get_stats_native() for counting

### Files Changed
- `rag_repository.py`: Added native methods
- `commands.py`: Added native CLI commands

### Usage
```bash
# Embed directly on an issue
tasker rag embed-native --type issue --id <issue_id>

# Search using native embeddings
tasker rag search-native issue "fix memory leak"
```
