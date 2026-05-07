# Issue #259: Automated Integrity and Self-Healing Logic

## Description

Implement the "Self-Healing Architecture" logic described in the v1.0 data model documentation (lines 240 and 465).

### Requirements

1.  **File Integrity Guard**:
    - Implement a startup or pre-task check that compares the `fileHash` on the physical disk with the `fileHash` stored in the `CodeFile` node.
    - If a mismatch is detected, trigger a "Re-scan" for that specific file.

2.  **Pre-Commit Policy Auditor**:
    - Implement logic where an Agent, before committing, queries for all `Policy` nodes linked to the `Project`.
    - The agent must evaluate its proposed change against these policies and use the `remediationStrategy` if a violation is found.

### Business Value
Ensures that the graph remains a "Single Source of Truth" that is always in sync with the actual source code, preventing agents from making decisions based on outdated models.

## Status: COMPLETED
