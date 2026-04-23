# Fix dependency add to support name lookup like component add

**Status**: COMPLETED
**Priority**: MEDIUM
**Labels**: enhancement, cli
**Created**: 2026-04-12

## Problem

Users can add issues by name using `tasker issue create "Title" -c backend`, but cannot add dependencies by name.

`tasker dependency add "Issue for test" ffa65e54` fails because it requires the full issue_id.

## Location

`src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

## Expected Behavior

```bash
# Both of these should work:
tasker dependency add "Issue for test" "Second issue"
tasker dependency add ffa65e54 06a514e5
```

## Current Behavior

```
Error resolving issue ID: Invalid issue ID format
```

## Suggestions

1. Add `resolve_issue_id` function similar to `resolve_component_id`
2. Support search by title, partial ID, or full UUID