# Issue #250: Align Intelligence Pillar (User, Agent, ReasoningNode, RAGEmbedding)

## Description

The "Intelligence Pillar" is the heart of Tasker's AI-native capabilities. This issue covers the alignment of nodes that track who is performing work (User/Agent) and how they are thinking (Reasoning/Embeddings).

### Required Changes

#### 1. `Agent` (n3)
- Properties: `id`, `name`, `role`, `status`, `capabilities`, `createdAt`.
- Ensure `role` and `status` use the correct Enums.

#### 2. `User` (n4)
- Implement `User` entity if missing.
- Properties: `id`, `username`, `email`, `role`, `githubHandle`, `createdAt`, `lastLogin`, `preferences`.

#### 3. `ReasoningNode` (n10)
- Properties: `id`, `thought`, `confidence`, `decisionType`.
- **Note**: The current implementation has `alternatives_considered` and other fields; ensure the core 4 documented properties are the primary ones and are in `camelCase`.

#### 4. `RAGEmbedding` (n11)
- Properties: `id`, `content`, `embedding`, `sourceType`, `modelInfo`.
- **Relationship**: `(Project)-[:DEFINES_CONTEXT]->(RAGEmbedding)`.

### Requirements
- Full migration to **camelCase** in the database layer.
- Update `reasoning_repository.py` and `rag_repository.py` to reflect these changes.
- Ensure `(User)-[:VALIDATES]->(ReasoningNode)` relationship is supported.

### Business Value
A well-defined Intelligence Pillar enables the "Reasoning Layer" of the graph, allowing the system to explain *why* a change was made and *who* (human or AI) authorized it.

## Status: COMPLETED
