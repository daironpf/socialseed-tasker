# Issue #381: CLI lacks circular dependency detection

## Description
The `tasker dependency add` command does not detect or prevent circular dependency chains. Users can create A→B→C→A cycles without any warning, which can lead to infinite loops in dependency resolution and confusing blocked-issue reports.

## Expected Behavior
When adding a dependency that would create a cycle, the CLI should detect the cycle, reject the operation, and display a clear error message explaining the conflict.

## Actual Behavior
The `dependency add` command accepts any dependency relationship without checking for cycles. No warning or rejection is issued.

## Steps to Reproduce
1. Create issues A, B, C
2. `tasker dependency add B --depends-on A`
3. `tasker dependency add C --depends-on B`
4. `tasker dependency add A --depends-on C` (this should be rejected)
5. Cycle is silently created

## Status: PENDING

## Priority: LOW

## Component
CLI, Dependency management

## Suggested Fix
Add graph cycle detection using DFS/BFS before creating each dependency. If a cycle would result, reject the operation and display a descriptive error message showing the cycle path.

## Impact
Users can accidentally create circular dependency chains that make the dependency graph inconsistent and complicate issue resolution tracking.

## Related Issues
- (none)

## Actual Status: Already Implemented

This issue is a false positive from the black-box test report. Circular dependency detection already exists:

1. **`add_dependency_action`** (`src/socialseed_tasker/application/actions.py:600`): Calls `_would_create_cycle()` which performs BFS traversal from `depends_on_id` to check if it can reach `issue_id` through existing `[:DEPENDS_ON]` edges. Raises `CircularDependencyError` with the cycle path if detected.

2. **CLI handling** (`src/socialseed_tasker/cli/commands/dependency_commands.py:121`): Catches `CircularDependencyError` and displays the cycle path, then exits with code 2.

3. **Tests exist** (`tests/unit/test_actions.py:324-339`): `test_raises_on_self_dependency` and `test_raises_on_circular_dependency` both pass.

## Verification
- `python -m pytest tests/unit/test_actions.py -k "circular or self_dependency"` → 2 passed
- Creating A→B→C→A is correctly rejected with `CircularDependencyError`
