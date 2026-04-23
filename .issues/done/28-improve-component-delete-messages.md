# Issue #28: Add Component Delete Confirmation and Interactive Mode

## Description

The `component delete` command requires the `--force` flag but doesn't provide clear feedback about why. When deleting a component with issues, the error message should be clearer and suggest the --force option.

### Requirements

- Improve error message when component has issues to clearly suggest `--force`
- Add interactive confirmation mode (prompt before delete unless --force is used)
- Add `--yes` short flag as alternative to `--force`
- Verify behavior in CLI tests

### Technical Details

File: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

Current error when component has issues:
```
Component 'xxx' has 3 issue(s). Use --force to delete anyway.
```

Should be more helpful:
```
Component 'xxx' has 3 issue(s) that will become unassigned.
Use --force to delete anyway, or --yes to confirm.
```

### Business Value

Prevents accidental deletion and improves user experience with clearer guidance.

## STATUS: COMPLETED