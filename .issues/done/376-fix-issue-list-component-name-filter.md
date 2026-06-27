# Issue #376: issue list --component filter fails with component name (requires UUID)

## Description
`tasker issue list -c "e-commerce"` returns "No issues found" even when issues exist under that component. Only UUID prefix or full UUID works. The `--component`/`-c` option claims to accept "component ID, name, or prefix" in the help text, but name resolution is not implemented.

## Expected Behavior
`tasker issue list -c "e-commerce"` should find issues for the component named "e-commerce" (using name-to-ID resolution internally).

## Actual Behavior
```
$ tasker issue list -c "e-commerce"
No issues found.
$ tasker issue list -c "1dfc14"
+--- ... (shows issues correctly)
```

## Steps to Reproduce
1. Create component `e-commerce` with 30 issues
2. Run `tasker issue list -c "e-commerce"`
3. Observe empty result
4. Run `tasker issue list -c "1dfc14"` (UUID prefix)
5. Observe correct results

## Status: COMPLETED

## Priority: LOW

## Component
CLI, Issue listing

## Suggested Fix
In `issue_commands.py:component_callback` or the list endpoint, when the `--component` value is not a valid UUID, resolve it by querying the component repository by name first, then use the resolved ID for filtering.

## Impact
Low. Users can always use UUID prefix or full ID. But the help text is misleading and new users will be confused when the name they gave during `component create` doesn't work as a filter.

## Related Issues
- (none)
