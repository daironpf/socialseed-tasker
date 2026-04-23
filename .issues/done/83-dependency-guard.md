# Issue #83: Dependency Guard

## Description

Implement real-time prevention of circular dependencies during issue creation. The current system detects circular dependencies but does not actively prevent them at creation time.

## Requirements

- Validate dependency creation in real-time (before saving)
- Detect circular dependencies using BFS bidirectional traversal
- Block creation if adding the dependency would create a cycle
- Return clear error message indicating which issue would cause the cycle
- Add CLI validation before creating dependencies
- Support "force" flag to bypass validation (for advanced users)

## Technical Details

### Algorithm
- Before adding dependency A->B, check if B can reach A via existing paths
- Use BFS from B; if A is found, adding A->B creates a cycle

### API Changes
- Add validation in `POST /dependencies` endpoint
- Return 400 with "CircularDependencyError" and cycle path

### CLI Changes
- Add validation in `tasker dependency add` command
- Show cycle path in error message

## Business Value

Maintains graph integrity by preventing invalid dependency structures. Agents can trust that the dependency graph is always acyclic.

## Status: COMPLETED