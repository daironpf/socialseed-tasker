# Issue #418: Add test command to CLI --help output

## Description
The documentation references a `test` command, but `tasker --help` does not list it. This creates a doc gap where users cannot discover how to run tests via the CLI.

## Expected Behavior
`tasker --help` should list a `test` command if one exists, or documentation should be updated to clarify the correct testing approach.

## Actual Behavior
`tasker --help` output does not include any `test` subcommand, leaving users confused about how to run tests through the CLI.

## Steps to Reproduce
1. Run `tasker --help`
2. Search for "test" in the command list
3. No test command found

## Status: COMPLETED

## Priority: LOW

## Component
CLI

## Suggested Fix
Either add a `tasker test` command, or update documentation to point users to `pytest` directly.

## Impact
Low. Users can still run `pytest` manually, but discoverability is reduced.

## Related Issues
- (none)

## Changes Made
- Removed reference to non-existent `tasker test` command in `.agent/skills/programming-agent-governance.md:27`
- Changed from "Run tests: `pytest` or `tasker test`" to "Run tests: `pytest`"

## Verification
- `tasker --help` no longer shows discrepancy with documentation
- `rg "tasker test" --include "*.md" .` shows no remaining references to the non-existent command
