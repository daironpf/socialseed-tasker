# Issue #374: Celery import at module level breaks CLI without [celery] extra

## Description
`cli/main.py` line 16 unconditionally imports `from celery.result import AsyncResult`, which means every invocation of the argparse-based CLI fails with `ModuleNotFoundError: No module named 'celery'` unless the `[celery]` extra is installed via pip.

The typer-based entry point (`cli/app.py`) does not have this issue because it doesn't import celery at module level.

## Expected Behavior
The CLI should work for basic commands (component list, issue create, etc.) without requiring the `[celery]` extra. The celery import should be lazy (inside the functions that actually use it).

## Actual Behavior
Running `tasker component list` with only `pip install -e .` (no extras) raises:
```
ModuleNotFoundError: No module named 'celery'
```

## Steps to Reproduce
1. Create a venv with `pip install -e .` (no extras)
2. Run `tasker component list`
3. Observe `ModuleNotFoundError: No module named 'celery'`

## Status: COMPLETED

## Priority: MEDIUM

## Component
CLI, Packaging/Dependencies

## Suggested Fix
Move `from celery.result import AsyncResult` and `from socialseed_tasker.workers.app import create_celery` into the `cmd_enqueue_task` and `cmd_task_status` functions that actually use them, making them lazy imports guarded by a try/except.

## Impact
Current users must always install with `pip install -e ".[celery]"` even if they never use background tasks. This is a poor DX and a silent dependency leak.

## Related Issues
- #200 CLI entry point not in PATH after installation
