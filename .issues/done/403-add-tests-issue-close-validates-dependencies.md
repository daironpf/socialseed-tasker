# Issue #403: Add tests for issue close dependency validation

## Description

The issue close endpoint correctly validates that all dependencies are CLOSED before allowing an issue to be closed. Issues with open dependencies are rejected. This behavior should be covered by automated tests to prevent regressions.

## Expected Behavior

Cannot close an issue that has OPEN or IN_PROGRESS dependencies.

## Actual Behavior

Works correctly — API returns an error when attempting to close an issue with open dependencies.

## Steps to Reproduce
1. Create issue A (OPEN)
2. Create issue B with dependency on A
3. Attempt to close B → should fail with dependency validation error
4. Close A
5. Attempt to close B → should succeed

## Status: PENDING

## Priority: LOW

## Component
API / Testing

## Suggested Fix
Add unit and integration tests for dependency validation on issue close.

## Impact
Prevents regressions in a critical business rule.
