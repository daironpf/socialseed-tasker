---
title: "RAG Context Window Manager (Token Pruning)"
component: "RAG Intelligence"
priority: "MEDIUM"
status: "TODO"
version: "v1.0.0"
---

# Issue #232: RAG Context Window Manager (Token Pruning)

## Description
When an agent queries the RAG system (`/api/v1/rag/search`), the returned nodes (especially large `CodeFile` nodes or long `ReasoningNode` thoughts) might exceed the agent's LLM context window limit. Tasker should proactively manage the size of the payload it returns to prevent agent token overflow errors.

## Acceptance Criteria
- [ ] Implement a `TokenEstimator` utility (using `tiktoken` or a rough character heuristic) in the RAG API.
- [ ] Add a `max_tokens` query parameter to the RAG search endpoint.
- [ ] Implement a `ContextPruner` that truncates or ranks RAG results so the total payload size never exceeds `max_tokens`.
- [ ] If a `CodeFile` is too large, the pruner should prioritize returning the matching `CodeSymbol` (e.g., just the function) rather than the entire file content.

## Technical Notes
- This ensures that agents remain stable even when retrieving data from massive codebases.
- The `ContextPruner` should prioritize the most relevant results (highest cosine similarity score) and drop the lowest scoring results until the payload fits.
