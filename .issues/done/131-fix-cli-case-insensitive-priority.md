# Fix CLI case-insensitive priority input

**Status**: OPEN
**Priority**: HIGH
**Labels**: bug, cli
**Created**: 2026-04-12

## Problem

The CLI command `tasker issue create -p high` fails with `ValueError: 'high' is not a valid IssuePriority`.

Users must use uppercase `-p HIGH`, which is not user-friendly.

## Location

`src/socialseed_tasker/entrypoints/terminal_cli/commands.py:340`

## Expected Behavior

The CLI should accept case-insensitive priority input (`high`, `HIGH`, `High`) and convert to the valid enum value automatically.

## Test Commands

```bash
# These should all work:
tasker -pw neoSocial issue create "Test" -c 1fa8d747 -p high
tasker -pw neoSocial issue create "Test" -c 1fa8d747 -p HIGH
tasker -pw neoSocial issue create "Test" -c 1fa8d747 -p High
```

## Suggestions

1. Convert input to uppercase before passing to `IssuePriority()` enum
2. Or use `@casefold()` for case-insensitive comparison
3. Show valid options in error message when invalid input provided