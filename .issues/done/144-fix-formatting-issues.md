# Fix formatting issues (I001, E501)

**Status**: COMPLETED
**Priority**: LOW
**Labels**: lint, formatting
**Created**: 2026-04-12

## Problem

The linter reports formatting issues that should be resolved for consistent code style.

## Issue Types

### I001: Import block is unsorted or un-formatted

Multiple files have unsorted imports:

1. `bootstrap/container.py` - lines 15, 196
2. `core/services/github_mirror.py` - line 7
3. `core/services/sync_engine.py` - line 7
4. `core/task_management/actions.py` - line 7
5. `entrypoints/terminal_cli/commands.py` - lines 74, 301, 1537
6. `entrypoints/web_api/routes.py` - lines 16, 22, 36, 37, 230, 1050

**Fix:** Run `ruff check --fix` to auto-sort imports, or manually organize.

### E501: Line too long (>120 characters)

1. `core/project_analysis/policy.py:216` - Line length 130
2. `entrypoints/web_api/routes.py:877` - Line length 137

**Fix:** Break long lines to conform to 120 char limit.

## Test Commands

```bash
.venv/Scripts/python.exe -m ruff check src/ --select I001,E501
.venv/Scripts/python.exe -m ruff check src/ --fix
```

## Expected Result

All formatting issues resolved.

## Status: PENDING