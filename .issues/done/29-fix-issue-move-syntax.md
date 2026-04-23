# Issue #29: Fix Issue Move Command Uses Wrong Option Name

## Description

The `issue move` command requires `--to` option but users naturally try to use the issue_id as the target component (e.g., `tasker issue move <issue> <component>`). The command should accept either positional argument for target component or make the syntax more intuitive.

### Requirements

- Add alias for `--to` option or make component ID a positional argument
- Update help text to show example usage
- Verify move command works in tests

### Technical Details

File: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

Current (requires --to):
```bash
tasker issue move <issue_id> --to <component_id>
```

Should allow:
```bash
tasker issue move <issue_id> <component_id>
# OR
tasker issue move <issue_id> --to <component_id>
```

### Business Value

Command should be intuitive. Users expect `move` to work like Unix `mv` (source dest).

## STATUS: COMPLETED