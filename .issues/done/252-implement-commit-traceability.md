# Issue #252: Implement Commit Node and Engineering History Traceability

## Description

The `Commit` node (n9) links the logical intent (Issues) with the physical changes (CodeFiles). Currently, the system lacks a dedicated `Commit` entity in the core domain.

### Required Entity: `Commit` (n9)
- Properties: `sha` (Primary ID), `message`, `authorName`, `authorEmail`, `timestamp`, `isAiGenerated`, `branch`, `additions`, `deletions`, `filesChanged`.

### Required Relationships (Traceability):
- **(Issue)-[:RESOLVED_BY]->(Commit)**: Links the requirement to the solution.
- **(Commit)-[:MODIFIED]->(CodeFile)**: Tracks exactly which files were changed in a version.
- **(Commit)-[:RESULTED_IN]<-(ReasoningNode)**: Links the physical change to the AI thought process.
- **(Commit)-[:VIOLATES]->(Policy)**: Tracks which commits broke governance rules.

### Requirements
- Create `Commit` entity in `src/socialseed_tasker/core/task_management/entities.py`.
- Implement `commit_repository.py` or extend `Neo4jTaskRepository` to handle Commit persistence.
- Ensure all properties use **camelCase**.

### Business Value
This node provides the **"Physical Trace"** of the project's evolution. It allows for "Time-Travel Audits" where you can ask: "Who changed this file, why did they do it (Reasoning), and did it pass our security policies (Policy)?"

## Status: COMPLETED
