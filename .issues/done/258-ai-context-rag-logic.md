# Issue #258: Advanced AI Context & RAG Pre-filtering

## Description

Implement the functional logic defined in the v1.0 data model "Implementation Notes" (line 402) to optimize the AI's understanding of the codebase.

### Requirements

1.  **RAG Pre-filtering**:
    - Update the RAG retrieval logic to allow filtering by `sourceType` (`CODE_SNIPPET`, `DOCUMENTATION`, `ARCH_DECISION`).
    - This reduces LLM hallucinations by providing only the relevant context type for a given query.

2.  **Architectural Context Builder**:
    - Implement a utility that uses the `(Issue)-[:AFFECTS]->(CodeSymbol)` relationship to automatically build the initial RAG context for an agent when it starts a task.

### Business Value
Reduces token usage and increases the accuracy of AI-proposed fixes by providing a highly targeted knowledge base instead of a generic search.

## Status: COMPLETED
