# Fix code quality issues (F541, F841, B904)

**Status**: COMPLETED
**Priority**: MEDIUM
**Labels**: lint, code-quality
**Created**: 2026-04-12

## Problem

The linter reports various code quality issues that should be addressed for cleaner code.

## Issue Types

### F541: f-strings without any placeholders

These should use regular strings instead of f-strings:

1. `commands.py:351` - `f"[error]Policy violations found:[/error]"`
2. `commands.py:360` - `f"[warning]Policy warnings:[/warning]"`
3. `commands.py:664` - `f"[error]Policy violations found:[/error]"`
4. `commands.py:673` - `f"[warning]Policy warnings:[/warning]"`
5. `github_mirror.py:106` - f-string without placeholders
6. `github_mirror.py:132` - f-string without placeholders

**Fix:** Remove `f` prefix from these strings.

### F841: Local variables assigned but never used

1. `commands.py:584` - `updated_issue` assigned but never used
2. `commands.py:619` - `updated_issue` assigned but never used
3. `github_mirror.py:93` - `reasons` assigned but never used

**Fix:** Either use the variable or remove the assignment.

### B904: Missing `raise ... from err` in except blocks

These exceptions should use `raise ... from err` to distinguish from errors in exception handling:

1. `commands.py:316` - IssueTitleValidationError
2. `commands.py:322` - IssueDescriptionValidationError
3. `commands.py:331` - ComponentNotFoundError
4. `commands.py:588` - ValueError
5. `commands.py:623` - ValueError
6. `commands.py:647` - ValueError
7. `commands.py:653` - ValueError
8. `commands.py:802` - ComponentNameValidationError
9. `commands.py:846` - ValueError
10. `commands.py:1035` - ValueError
11. `commands.py:1552` - Exception
12. `routes.py:242` - IssueTitleValidationError
13. `routes.py:247` - IssueDescriptionValidationError
14. `routes.py:748` - Exception
15. `routes.py:775` - Exception
16. `routes.py:1061` - ComponentNameValidationError
17. And more...

**Fix:** Add `from err` or `from None` to raise statements:

```python
except SomeError as e:
    raise typer.Exit(code=1) from e  # or from None
```

## Test Commands

```bash
.venv/Scripts/python.exe -m ruff check src/ --select F541,F841,B904
```

## Expected Result

All code quality issues resolved.

## Status: PENDING