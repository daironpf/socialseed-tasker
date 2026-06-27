# Issue #256: Recursive and Domain-Driven Specialty Relationships

## Description

The v1.0 model includes specific relationships that enable "Domain-Driven Dispatching" and "Traceability Audits." These must be explicitly implemented in the logic layer.

### Required Relationships

#### 1. Recursive/Hierarchical
- **`CHILD_OF`**: `(CodeSymbol)-[:CHILD_OF]->(CodeSymbol)` (Classes -> Methods).
- **`PARENT_OF`**: `(Commit)-[:PARENT_OF]->(Commit)` (Git history tree).

#### 2. Domain Specialty (Dispatching)
- **`SPECIALIST_IN`**: `(Agent)-[:SPECIALIST_IN]->(Component)`.
- **`INTERESTED_IN`**: `(Agent)-[:INTERESTED_IN]->(Label)`.
- **`SUGGESTS`**: `(ReasoningNode)-[:SUGGESTS]->(Label)`.

#### 3. Semantic Linkage
- **`HAS_VECTOR`**: `(CodeSymbol)-[:HAS_VECTOR]->(RAGEmbedding)`.

### Requirements
- Update `Neo4jTaskRepository` to provide methods for creating and querying these relationships.
- Update `ArchitecturalAnalyzer` or the dispatching logic to utilize `SPECIALIST_IN` when assigning agents to issues.

### Business Value
These relationships transform the graph from a simple database into an "Active Control Plane," where the system knows which agent is best for each task based on their past work and expertise.

## Status: COMPLETED
