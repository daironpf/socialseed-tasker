# Issue #340: Cycle detection message repeats same UUID twice

## Description
When a circular dependency is detected, the error message shows the same issue UUID twice in the cycle path, which is confusing.

## Expected Behavior
Each UUID should appear only once in the cycle path.

## Actual Behavior
The terminal node (starting point of the cycle) is listed twice at the end of the path.

## Steps to Reproduce
1. Run `tasker dependency add 9789e66e 3b05cb5c` (where 3b05cb5c already depends on 9789e66e)
2. Observe cycle path shows same UUID twice

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Filter terminal node (the starting point of the cycle) from being listed twice at the end

## Impact
Minor confusion when reading error messages

## Related Issues
-
