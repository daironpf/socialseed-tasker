# Remove unused imports (F401)

**Status**: COMPLETED
**Priority**: MEDIUM
**Labels**: lint, cleanup
**Created**: 2026-04-12

## Problem

The linter reports multiple F401 errors for imported but unused modules. These should be removed to clean up the codebase.

## Locations

### 1. bootstrap/container.py

```python
F401: pathlib.Path imported but unused (line 11)
F401: typing.Literal imported but unused (line 12)
```

### 2. core/services/connectivity_manager.py

```python
F401: collections.defaultdict imported but unused (line 11)
```

### 3. core/services/github_issue_mapper.py

```python
F401: time imported but unused (line 10)
F401: uuid.UUID imported but unused (line 13)
```

### 4. core/services/markdown_transformer.py

```python
F401: datetime.datetime imported but unused (line 11)
```

### 5. core/task_management/actions.py

```python
F401: ConstraintLevel imported but unused (line 22)
```

### 6. entrypoints/terminal_cli/commands.py

```python
F401: uuid.UUID imported but unused (line 310)
```

### 7. entrypoints/web_api/app.py

```python
F401: fastapi.HTTPException imported but unused (line 15)
F401: fastapi.Response imported but unused (line 15)
F401: httpx imported but unused (line 236)
```

### 8. entrypoints/web_api/routes.py

```python
F401: PolicyViolationError imported but unused (line 25)
F841: related_nodes assigned but never used (line 572)
```

## Fix Strategy

Run `ruff check --fix src/` to auto-remove unused imports. For manually unused variables like `related_nodes`, remove the assignment or use `_` prefix.

## Test Commands

```bash
.venv/Scripts/python.exe -m ruff check src/ --select F401
.venv/Scripts/python.exe -m ruff check src/ --fix
```

## Expected Result

All F401 errors resolved.

## Status: PENDING