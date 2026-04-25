# Issue #25: Remove sys.path Hack from CLI Commands

## Description

`src/socialseed_tasker/entrypoints/terminal_cli/commands.py` contains a `sys.path.insert` hack at lines 19-22 that adds the `src/` directory to the Python path. This is a leftover from when the file was designed to run as a standalone script. In an installed package, this is unnecessary and can cause import order issues.

### Requirements

- Remove the `sys.path` manipulation block from `commands.py`
- Ensure all imports work correctly when the package is installed
- Verify the CLI still works after removal with `tasker --help` and `tasker issue list`
- If any imports break, fix them by ensuring proper package structure

### Technical Details

File: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

Remove these lines:
```python
# Add src to path for imports when running as script
_src_path = str(Path(__file__).parent.parent.parent.parent / "src")
if _src_path not in sys.path:
    sys.path.insert(0, _src_path)
```

The entry point in `pyproject.toml` already points to `socialseed_tasker.entrypoints.terminal_cli.app:main_entry`, which means the package is installed and imports work normally.

Also remove the now-unused `sys` and `Path` imports if they're no longer needed:
```python
import sys  # Remove if only used for sys.path
from pathlib import Path  # Remove if only used for _src_path
```

Expected file paths:
- `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

### Business Value

Cleaner code, no hidden side effects from path manipulation, eliminates E402 linting warnings, and ensures the package works correctly in all installation scenarios (editable, wheel, venv).

## Status: COMPLETED
