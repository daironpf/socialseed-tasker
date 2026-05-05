# Issue #240: Increase test coverage for RAG repository to 70%

## Description
The RAG embedding repository (rag_repository.py) has only 17% test coverage with 121 statements and 100 missing lines. Vector search operations are mostly untested.

## Expected Behavior
RAG module should have comprehensive tests for semantic search.

## Actual Behavior
Only 17% coverage - missing tests for:
- Similarity search thresholds
- Embedding chunking strategies
- Vector index queries

## Steps to Reproduce
1. Run: `pytest tests/ --cov=socialseed_tasker/storage/graph_database/rag_repository.py`
2. Observe: Low coverage report

## Status: COMPLETED

## Priority: MEDIUM

## Component
CORE

## Suggested Fix
Add tests for:
- `test_similarity_search_threshold_filtering`
- `test_chunk_by_paragraph_strategy`
- `test_vector_index_query_performance`

## Impact
RAG semantic search may produce incorrect results.

## Related Issues
- #124 (previous coverage effort)