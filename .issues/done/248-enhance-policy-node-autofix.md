# Issue #248: Enhance Policy Node with Auto-Fix Capabilities

## Description

The current `Policy` implementation in `policy.py` only supports detection of architectural violations. To reach the v1.0 goal of "Autonomous Quality Assurance," we need to add fields that allow AI agents to remediate violations automatically.

### Requirements

1.  **Update `Policy` Entity**:
    - Add `targetScope`: Enum `[CODE_SYMBOL, COMPONENT, COMMIT, PROJECT]`.
    - Add `logicDefinition`: JSON string or structured object defining the validation logic.
    - Add `remediationStrategy`: String instructions for the Agent on how to resolve a violation.
    - Add `autofixTemplate`: Code template or command for automatic correction.

2.  **Update Neo4j Layer**:
    - Update the `Policy` node properties in `queries.py` and `repositories.py` (ensure camelCase naming).
    - Add relationships if necessary (e.g., `(Policy)-[:APPLIES_TO]->(Component)`).

3.  **Update Policy Engine**:
    - Ensure the `PolicyEngine` in `policy.py` can expose these new fields to the agents during the validation phase.

### Business Value

Allows for "Self-Healing Architecture." Instead of just blocking a PR because of a violation, the system can provide the exact code change needed to fix it, significantly reducing the friction of architectural enforcement and increasing developer (and agent) productivity.

## Status: COMPLETED
