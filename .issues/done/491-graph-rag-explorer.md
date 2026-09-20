# Issue #491: Implement Graph RAG & Semantic Memory Explorer

## Description
Resolved issues store solution embeddings in Neo4j to enable long-term memory and retrieval for agents. A visual search engine is needed for human engineers and agents to query past technical solutions using natural language.

## Expected Behavior
- Natural language search input with vector similarity threshold controls
- Ranked results displaying past issues, embedding similarity score %, and solution summaries
- Sub-graph preview visualizing the context nodes (Functions, Components, Issues) used to build the answer

## Status: DONE

## Priority: HIGH

## Component
Frontend / Graph / RAG Explorer

## Implementation Plan
1. Create `GraphRAGExplorerView.vue` view
2. Build natural language search input with threshold slider
3. Implement ranked results display with similarity scores
4. Add solution summaries for each result
5. Build sub-graph preview visualization
6. Create RAG-specific types and store
7. Add i18n keys for RAG explorer
8. Add navigation route

## Acceptance Criteria
- [x] Natural language search input
- [x] Vector similarity threshold controls
- [x] Ranked results with similarity score %
- [x] Solution summaries per result
- [x] Sub-graph context preview
- [x] i18n support (EN + ES)

## Verification
- Navigate to Graph RAG Explorer
- Enter natural language query
- Adjust similarity threshold
- See ranked results with scores
- Click result to see sub-graph preview
- Context nodes visualized correctly

## Files Created
- `frontend/src/types/rag.ts` — RAGResult, RAGContextNode, RAGSearchResponse, RAGMetrics
- `frontend/src/stores/ragStore.ts` — Pinia store with 6 mock solutions, search, metrics
- `frontend/src/views/GraphRAGExplorerView.vue` — Search input, threshold slider, ranked results, sub-graph SVG

## Files Modified
- `frontend/src/router/index.ts` — Added `/rag` route
- `frontend/src/components/layout/Sidebar.vue` — Added "Graph RAG Explorer" nav item
- `frontend/src/components/layout/AppHeader.vue` — Added header title mapping
- `frontend/src/locales/en.json` — Added 23 rag i18n keys
- `frontend/src/locales/es.json` — Added 23 rag i18n keys (Spanish)

## Related Issues
- #490 (Policy Sandbox), #492 (Code-as-Graph Overlay)
