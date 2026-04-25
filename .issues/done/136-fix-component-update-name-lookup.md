# Fix component update to support name lookup

**Status**: COMPLETED
**Priority**: HIGH
**Labels**: bug, cli
**Created**: 2026-04-12

## Problem

The CLI command `tasker component update backend -n "New Name"` fails with "Component 'backend' not found."

Users cannot update components by name, only by UUID.

## Location

`src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

## Expected Behavior

`tasker component update backend -n "Backend API"` should work.

## Test Commands

```bash
tasker -pw neoSocial component update backend -n "Backend Updated"
```

## Current Behavior

```
Component 'backend' not found.
```

## Suggestions

1. Use `resolve_component_id` in `component_update` function
2. Allow search by name, partial ID, or full UUID