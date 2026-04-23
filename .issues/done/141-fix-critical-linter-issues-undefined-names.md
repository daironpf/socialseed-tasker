# Fix critical linter issues - undefined names

**Status**: COMPLETED
**Priority**: HIGH
**Labels**: lint, bug
**Created**: 2026-04-12

## Problem

The linter (`ruff`) reports multiple critical F821 errors for undefined names that cause runtime errors.

## Locations

### 1. commands.py - Missing UUID import for type hints

**File:** `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

- Line 96: `def resolve_component_id(partial_id: str, repo: TaskRepositoryInterface) -> UUID:` - `UUID` not imported
- Line 140: `def resolve_issue_id(partial_id: str, repo: TaskRepositoryInterface) -> UUID:` - `UUID` not imported

**Fix:** Add at the top of the file:

```python
from uuid import UUID
```

### 2. actions.py - Missing Any import in Protocol

**File:** `src/socialseed_tasker/core/task_management/actions.py`

- Line 186: `list[dict[str, Any]]` - `Any` not defined
- Line 198: `dict[str, Any]` - `Any` not defined
- Line 207: `dict[str, Any]` - `Any` not defined
- Line 574: `policy_engine: Any = None` - `Any` not defined

**Fix:** Add to imports:

```python
from typing import Any
```

### 3. container.py - Missing Any import

**File:** `src/socialseed_tasker/bootstrap/container.py`

- Line 52: `**kwargs: Any` - `Any` not defined

**Fix:** Add to imports:

```python
from typing import Any, TYPE_CHECKING
```

## Test Commands

```bash
.venv/Scripts/python.exe -m ruff check src/
```

## Expected Result

All F821 errors resolved, no runtime errors from undefined names.

## Status: PENDING