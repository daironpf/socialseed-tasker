# Issue #180 - Add --version Flag to CLI

## Description

The CLI does not have a `--version` flag, making it difficult for users to verify which version they're running.

## Problem

```bash
$ pip install socialseed-tasker
$ tasker --version
Usage: tasker [OPTIONS] COMMAND [ARGS]...
Try 'tasker --help' for help.
+------------------------------------------------------------------------------+
| No such option: --version                                                    |
+------------------------------------------------------------------------------+
```

Users must use `pip show socialseed-tasker` or import the package in Python to check the version.

## Root Cause

The CLI application (`src/socialseed_tasker/entrypoints/terminal_cli/app.py`) does not implement the `--version` option.

## Expected Behavior

```bash
$ tasker --version
socialseed-tasker 0.8.1
```

## Implementation Steps

### Step 1: Update app.py to add version option

```python
import socialseed_tasker

@click.group()
@click.version_option(
    version=socialseed_tasker.__version__,
    prog_name="tasker",
    package_name="socialseed-tasker"
)
def main():
    """SocialSeed Tasker - Graph-native task management for AI agents."""
    pass
```

### Step 2: Verify the version is correctly imported

Check `src/socialseed_tasker/__init__.py`:
```python
__version__ = "0.8.1"
```

### Step 3: Test the CLI

```bash
$ tasker --version
# Should display: socialseed-tasker 0.8.1
```

### Step 4: Update documentation

Add the `--version` flag to CLI documentation in README.

## Affected Files

- `src/socialseed_tasker/entrypoints/terminal_cli/app.py`

## Verification

```bash
$ tasker --version
socialseed-tasker 0.8.1

$ tasker --help
# Should show version info in help output
```

## Status: COMPLETED