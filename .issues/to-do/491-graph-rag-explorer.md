# Issue #491: Implement Graph RAG & Semantic Memory Explorer

## Description
Resolved issues store solution embeddings in Neo4j to enable long-term memory and retrieval for agents. A visual search engine is needed for human engineers and agents to query past technical solutions using natural language.

## Expected Behavior
- Natural language search input with vector similarity threshold controls
- Ranked results displaying past issues, embedding similarity score %, and solution summaries
- Sub-graph preview visualizing the context nodes (Functions, Components, Issues) used to build the answer

## Status: PENDING

## Priority: HIGH

## Component
Frontend / Graph / RAG Explorer

## Implementation Plan
1. Create `GraphRAGExplorer.vue` view
2. Build natural language search input with threshold slider
3. Implement ranked results display with similarity scores
4. Add solution summaries for each result
5. Build sub-graph preview visualization
6. Create RAG-specific types and store
7. Add i18n keys for RAG explorer
8. Add navigation route

## Acceptance Criteria
- [ ] Natural language search input
- [ ] Vector similarity threshold controls
- [ ] Ranked results with similarity score %
- [ ] Solution summaries per result
- [ ] Sub-graph context preview
- [ ] i18n support

## Verification
- Navigate to Graph RAG Explorer
- Enter natural language query
- Adjust similarity threshold
- See ranked results with scores
- Click result to see sub-graph preview
- Context nodes visualized correctly

## Related Issues
- #490 (Policy Sandbox), #492 (Code-as-Graph Overlay)
