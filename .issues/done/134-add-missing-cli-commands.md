# Add missing CLI commands

**Status**: OPEN
**Priority**: MEDIUM
**Labels**: enhancement, cli
**Created**: 2026-04-12

## Problem

Several CLI commands are missing that exist in the API. Users expect feature parity between CLI and API.

## Missing Commands

### Component commands
- `tasker component delete <id>` - Delete a component
- `tasker component update <id>` - Update component details
- `tasker component show <id>` - Show component details

### Dependency commands
- `tasker dependency list` - List all dependencies (currently requires issue_id)
- `tasker dependency blocked` - List all blocked issues

### Analysis commands
- `tasker analyze root-cause` - Tested but requires closed issues to analyze

## Location

`src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

## Expected Behavior

The CLI should have feature parity with the API.

## Suggestions

1. Implement component delete with confirmation
2. Implement component show with detailed view
3. Implement component update (name, description, project)
4. Implement `dependency list` without required issue_id (show all)
5. Implement `dependency blocked` to show issues with blockers