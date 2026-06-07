# Issue #413: Duplicate dependency accepted silently

## Description
When running `tasker dependency add` twice with the same arguments, the second call succeeds instead of rejecting the duplicate. The Neo4j backend (Cypher MERGE) deduplicates at the storage level, making the second add a no-op, but the CLI returns a success message ("Dependency added: X -> Y") as if it created a new relationship.

## Expected Behavior
The CLI should detect that the dependency already exists and either:
- Return a clear message: "Dependency already exists: X -> Y"
- Or skip with a non-zero exit code indicating no-op

## Actual Behavior
Second `dependency add` with same arguments returns:
```
Dependency added: X -> Y
```
with exit code 0, implying a new dependency was created.

## Steps to Reproduce
1. `tasker dependency add <issue-id> --depends-on <dep-id>` (first time — succeeds)
2. `tasker dependency add <issue-id> --depends-on <dep-id>` (second time — also succeeds silently)

## Status: DONE

## Priority: LOW

## Component
CLI — dependency add command

## Suggested Fix
Before creating the DEPENDS_ON relationship, query if it already exists:
```
MATCH (a:Issue {id: $fromId})-[r:DEPENDS_ON]->(b:Issue {id: $toId})
RETURN r
```
If found, print "Dependency already exists" and exit with code 0 (or 1 for skip).

## Impact
Low — no data corruption (Neo4j dedup), but misleading UX for scripted workflows.

## Related Issues
- (none)

## Changes Made
- Added `DuplicateDependencyError` exception in `application/actions.py`
- Added duplicate check in `add_dependency_action()`: queries existing dependencies via `repository.get_dependencies()` before creating
- CLI: catches `DuplicateDependencyError` and prints warning message with exit code 0
- API: catches `DuplicateDependencyError` and returns HTTP 409 Conflict
- Added unit test `test_raises_on_duplicate_dependency` in `tests/unit/test_actions.py`

## Verification
- [x] Unit test `test_raises_on_duplicate_dependency` passes (FakeRepository correctly simulates duplicate state)
- [x] CLI shows "Dependency already exists: X -> Y" on duplicate
- [x] API returns 409 Conflict with descriptive message on duplicate
