# Fix component delete to support name lookup

**Status**: COMPLETED
**Priority**: MEDIUM
**Labels**: bug, cli
**Created**: 2026-04-12

## Problem

The CLI command `tasker component delete backend` should work (like `tasker component show backend`), but the delete command expects a full UUID or partial ID.

## Location

`src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

## Expected Behavior

```bash
# Should work like component show:
tasker component delete backend
tasker component delete 1fa8d747
```

## Current Behavior

Potentially requires full UUID.

## Suggestions

1. Use `resolve_component_id` in `component_delete` function
2. Follow same pattern as `component_show`