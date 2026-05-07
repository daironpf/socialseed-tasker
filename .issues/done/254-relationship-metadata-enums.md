# Issue #254: Implement Relationship-Level Properties and Global Enums

## Description

In the v1.0 Graph Model, relationships are not just connections; some carry critical metadata. This issue focuses on ensuring those properties are persisted and that all system Enums are synchronized.

### Required Changes

#### 1. Relationship Properties
- **`VALIDATES`**: Add `{approved: Boolean, comment: String}` to the relationship between `User` and `ReasoningNode`.
- **`MODIFIED`**: Add `{type: Enum[ADDED, MODIFIED, DELETED]}` to the relationship between `Commit` and `CodeFile`.
- **`HAS_VECTOR`**: Ensure potential metadata for vector linkage is supported.

#### 2. Global Enums Synchronization
Define/Update central Enums to match documentation:
- `Visibility`: `PUBLIC`, `PRIVATE`.
- `ProjectStatus`: `ACTIVE`, `ARCHIVED`.
- `AgentRole`: `DEVELOPER`, `TESTER`, `ARCHITECT`.
- `Severity`: `INFO`, `WARNING`, `BLOCKER`.
- `TargetScope`: `CODE_SYMBOL`, `COMPONENT`, `COMMIT`, `PROJECT`.

### Requirements
- Update `queries.py` to support `SET` operations on relationships.
- Ensure the API and Repositories can handle these relationship-level attributes.

### Business Value
Relationship properties like `approved` on `VALIDATES` are the backbone of the Human-in-the-Loop system, providing a clear audit trail of who authorized what and why.

## Status: COMPLETED
