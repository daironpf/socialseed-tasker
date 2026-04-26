# Issue #186: Refactor CLI Commands into Modular Architecture

## Description

The `commands.py` file has grown to 1782 lines, making it difficult to maintain, test, and navigate. The file contains all CLI commands mixed with helper functions, making the codebase harder to understand and extend.

## Problem

Current structure:
```
src/socialseed_tasker/entrypoints/terminal_cli/
├── app.py              # Entry point
├── commands.py         # 1782 lines - EVERYTHING here
└── __init__.py
```

All commands (issue, component, dependency, analyze, project, status, seed) and their helper functions (tables, formatters, credentials) are in a single file.

## Expected Structure

```
src/socialseed_tasker/entrypoints/terminal_cli/
├── app.py                    # Main entry point
├── __init__.py
├── commands/                 # New commands directory
│   ├── __init__.py          # Export all commands
│   ├── issues.py            # Issue commands (~250 lines)
│   ├── components.py        # Component commands (~200 lines)
│   ├── dependencies.py      # Dependency commands (~150 lines)
│   ├── analyze.py           # Analysis commands (~100 lines)
│   ├── project.py           # Project detection commands (~100 lines)
│   ├── status.py            # Status commands (~50 lines)
│   └── seed.py              # Seed commands (~50 lines)
├── formatters/              # Output formatters
│   ├── __init__.py
│   ├── tables.py            # Table generators
│   └── panels.py            # Panel/formatters
└── utils/                   # Shared utilities
    ├── __init__.py
    ├── credentials.py       # Credential management
    └── resolver.py          # ID resolution helpers
```

## Implementation Steps

### Step 1: Create directory structure

```bash
mkdir -p src/socialseed_tasker/entrypoints/terminal_cli/commands
mkdir -p src/socialseed_tasker/entrypoints/terminal_cli/formatters
mkdir -p src/socialseed_tasker/entrypoints/terminal_cli/utils
```

### Step 2: Move helper functions

Extract to new modules:
- `tables.py`: `_issues_table()`, `_components_table()`, `_dependencies_table()`
- `panels.py`: Panel helpers
- `credentials.py`: `_load_saved_credentials()`, `_save_credentials()`, etc.
- `resolver.py`: `resolve_component_id()`, `resolve_issue_id()`

### Step 3: Segment commands

Create individual command files:
- `issues.py`: All issue_* functions with @issue_app.command decorators
- `components.py`: All component_* functions
- `dependencies.py`: All dependency_* functions
- `analyze.py`: All analyze_* functions
- `project.py`: Project detection commands
- `status.py`: Status commands
- `seed.py`: Seed commands

### Step 4: Update imports in app.py

```python
from socialseed_tasker.entrypoints.terminal_cli.commands import (
    issue_app, component_app, dependency_app, analyze_app,
    project_app, status_app, seed_app
)
```

### Step 5: Create __init__.py exports

```python
# commands/__init__.py
from .issues import issue_app
from .components import component_app
from .dependencies import dependency_app
from .analyze import analyze_app
from .project import project_app
from .status import status_app
from .seed import seed_app

__all__ = [
    "issue_app",
    "component_app",
    "dependency_app",
    "analyze_app",
    "project_app",
    "status_app",
    "seed_app",
]
```

## Benefits

1. **Maintainability**: Smaller, focused files are easier to understand
2. **Testability**: Can unit test each command module independently
3. **Extensibility**: Easy to add new commands to their own module
4. **Navigation**: IDE can navigate faster with logical structure
5. **Onboarding**: New developers understand architecture faster

## Status: PENDING

## Priority
MEDIUM

## Component
CLI

## Affected Files

- `src/socialseed_tasker/entrypoints/terminal_cli/commands.py` (split)
- `src/socialseed_tasker/entrypoints/terminal_cli/app.py` (update imports)

## Related Issues

- #184: Improve CLI Intuitiveness (recently resolved)
- #183: Reduce Setup Friction (recently resolved)