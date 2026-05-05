# Issue #241: Fix datetime.utcnow() deprecation warnings

## Description
Pytest shows deprecation warnings for `datetime.datetime.utcnow()` which is deprecated in Python 3.14+ and scheduled for removal.

## Expected Behavior
Use timezone-aware objects: `datetime.now(datetime.UTC)`

## Actual Behavior
```
DeprecationWarning: datetime.datetime.utcnow() is deprecated and scheduled 
for removal in a future version.
```

## Steps to Reproduce
1. Run: `pytest tests/ -v`
2. Observe: DeprecationWarning in output

## Status: COMPLETED

## Priority: LOW

## Component
DOCKER

## Suggested Fix
Replace all instances of `datetime.utcnow()` with `datetime.now(datetime.UTC)` in all modules:
- `core/task_management/actions.py`
- `core/task_management/entities.py`
- `storage/graph_database/driver.py`
- `entrypoints/web_api/routes.py`

## Impact
Future Python versions will break the code.

## Related Issues
N/A