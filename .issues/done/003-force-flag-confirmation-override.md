# Issue #003 - Force Flag Doesn't Skip Confirmation in tasker init

## Description

`tasker init --force` still asks for overwrite confirmation when an existing `.agent` directory is detected, defeating the purpose of the `--force` flag.

## Expected Behavior

`tasker init --force` should skip all confirmation prompts and overwrite existing files without asking.

## Actual Behavior

```bash
$ tasker init . --force
Existing Tasker project detected at: /path/to/project
Using --force will overwrite current project configuration (.agent/tasker/ files, ROADMAP.md, VERSIONS.md).
Continue overwriting? [y/N]:  # <-- Still asks for confirmation!
```

The `--force` flag is ignored and the CLI still asks for user confirmation.

## Steps to Reproduce

1. Create a directory with existing `.agent/` folder
2. Run `tasker init . --force`
3. Observe that confirmation prompt still appears

## Root Cause

The `--force` flag is defined but not checked before the confirmation prompt. The code path doesn't branch based on the force parameter.

## Affected Files

- `src/socialseed_tasker/entrypoints/cli/init_command.py`
- `src/socialseed_tasker/core/system_init/scaffolder.py`

## Suggested Fix

1. **Check force flag before confirmation**:
   ```python
   if not force and os.path.exists('.agent'):
       if not click.confirm('Continue overwriting?'):
           return
   ```

2. **Or log a warning instead of prompting**:
   ```python
   if force and os.path.exists('.agent'):
       logger.warning("Overwriting existing .agent directory (--force)")
   ```

## Impact

Minor UX issue in automated workflows. Users expect `--force` to skip confirmations but it doesn't.

## Priority: LOW

## Component: CLI

## Status: COMPLETED

## Resolution

Modified `_run_scaffold()` to remove the confirmation prompt when `force=True`:
- When `force=True`, the code now simply logs a warning message
- No confirmation prompt is shown
- The scaffold proceeds directly to overwriting files

## Verification

```bash
$ tasker init . --force --yes
# Shows warning "Using --force to overwrite..." but no confirmation prompt
# Scaffold completes successfully
```
