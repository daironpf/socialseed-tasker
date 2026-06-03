# Issue #393: code-graph scan requires explicit PATH argument with no default

## Description
The `tasker code-graph scan` command requires an explicit `PATH` argument and fails with `Error: Missing parameter: path` when called without one. There is no default to the current directory (`.`).

## Expected Behavior
`tasker code-graph scan` (without arguments) should default to scanning the current directory (`.`), as this is the most common use case.

## Actual Behavior
Running `tasker code-graph scan` without arguments produces: `Error: Missing parameter: path`

## Steps to Reproduce
1. Run: `tasker code-graph scan`
2. Observe: `Error: Missing parameter: path`
3. Run: `tasker code-graph scan .` (succeeds)

## Status: PENDING

## Priority: LOW

## Component
CLI (`code_graph_commands.py`)

## Suggested Fix
Make the `PATH` argument optional in the Typer command definition with a default of `"."` (current directory). Update the function signature and any help text accordingly.

## Impact
Minor. The command works correctly when the path is provided. This is a UX polish improvement to match user expectations.

## Related Issues
- (none)

## Changes Made
[Leave empty]

## Verification
[Leave empty]
