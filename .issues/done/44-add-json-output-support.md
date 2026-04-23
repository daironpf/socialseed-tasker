# Issue #44: Add --json output option to all CLI list commands

## Description

Currently only some commands support `--json` output. This should be standardized across all list commands for better scripting and integration with external tools.

### Requirements

- Add `--json` option to: component list, issue list, dependency list
- Ensure JSON output is valid and properly formatted
- Include proper exit codes (0 for success, non-zero for errors)

### Current State

- `tasker issue list --json` - Works ✓
- `tasker component list --json` - Works ✓
- `tasker dependency list --json` - Now available ✓ (added)
- `tasker analyze root-cause` - Not available (low priority, can be added later)

**Resolution**: Added `--json` option to `dependency list` command.

## Status: COMPLETED