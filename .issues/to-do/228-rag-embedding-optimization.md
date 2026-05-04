---
title: "RAG Embedding Storage Optimization"
component: "RAG Intelligence"
priority: "HIGH"
status: "TODO"
version: "v1.0.0"
---

# Issue #228: RAG Embedding Storage Optimization

## Description
Currently, RAG embeddings are stored in a separate `RAGEmbedding` node and linked to their source documents (`Issue`, `CodeSymbol`, etc.). To optimize query performance and reduce graph traversal hops (hops), the embedding vectors should be stored directly on the primary nodes.

## Acceptance Criteria
- [ ] Add `embedding` property (List[Float]) directly to `Issue`, `CodeSymbol`, and `ReasoningNode` schemas.
- [ ] Update the Vector Index creation commands in `GRAPH_MODEL.md` to index the specific labels (e.g., `CREATE VECTOR INDEX issue_embeddings FOR (n:Issue) ON n.embedding`).
- [ ] Refactor the `RAGRepository` to store vectors on the source nodes instead of creating `RAGEmbedding` nodes.
- [ ] Create a migration script to merge existing `RAGEmbedding` vectors into their parent nodes.
- [ ] Update RAG search queries to return the native nodes directly, avoiding the `(RAGEmbedding)-[:EMBEDS]->(Source)` hop.

## Technical Notes
- Neo4j 5.x allows multiple vector indexes for different node labels.
- This will significantly simplify Cypher queries and improve retrieval speeds during Agent context gathering.
