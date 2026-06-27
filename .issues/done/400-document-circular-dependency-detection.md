# Issue #400: Document circular dependency detection feature

## Description

The circular dependency detection feature works correctly. When attempting to create a circular DEPENDS_ON relationship, the API returns a clear `CIRCULAR_DEPENDENCY` error with the full cycle path. This should be documented and tested.

## Expected Behavior

Circular dependencies are detected and rejected with a clear error message showing the cycle path.

## Actual Behavior

Works correctly — returns `{"error":{"code":"CIRCULAR_DEPENDENCY","message":"...would create a cycle: X -> A -> B -> Y"}}`.

## Steps to Reproduce
1. Create issue A -> B -> C dependencies
2. Attempt to add C -> A dependency (circular)
3. Observe `CIRCULAR_DEPENDENCY` error with cycle path

## Status: PENDING

## Priority: LOW

## Component
GRAPH_ENGINE / Documentation

## Suggested Fix
Add unit tests for cycle detection and document the feature in API reference.

## Impact
Ensures the circular detection feature remains reliable and is discoverable by users.
