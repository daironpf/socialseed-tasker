# Issue #001 - Unicode Encoding Error in CLI on Windows

## Description

`tasker init` fails with `UnicodeEncodeError` when output contains special characters (arrows →, emojis) on Windows with non-UTF-8 default encoding. The error occurs because the CLI doesn't handle character encoding properly.

## Expected Behavior

`tasker init` should complete successfully on Windows without requiring manual encoding configuration.

## Actual Behavior

```bash
$ tasker init .
Error: 'charmap' codec can't encode character '\u2192' in position 23: character maps to <undefined>
```

The initialization fails when trying to display Unicode characters in the terminal output.

## Steps to Reproduce

1. Open a standard Windows command prompt (not PowerShell with UTF-8 configured)
2. Navigate to a test directory
3. Run `tasker init .`
4. Observe the UnicodeEncodeError

## Root Cause

The CLI doesn't set `PYTHONIOENCODING=utf-8` or use `chcp 65001` before displaying output. Windows terminals default to a non-UTF-8 codepage that can't handle special characters.

## Affected Files

- `src/socialseed_tasker/entrypoints/cli/main.py`
- `src/socialseed_tasker/core/system_init/init_command.py`

## Suggested Fix

1. **Auto-detect and set encoding** in CLI entrypoint:
   ```python
   import sys
   import io
   if sys.platform == 'win32':
       sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
   ```

2. **Or set environment variable** before CLI execution:
   ```python
   os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
   ```

3. **Or use `chcp 65001`** in a wrapper script for Windows

## Impact

Prevents `tasker init` from completing on Windows without manual encoding configuration. Users must run `chcp 65001` or set `PYTHONIOENCODING=utf-8` before using the CLI.

## Priority: HIGH

## Component: CLI

## Status: COMPLETED

## Resolution

Added `_setup_windows_encoding()` function in `init_command.py` that:
1. Sets Windows console codepage to UTF-8 (65001)
2. Wraps `sys.stdout` and `sys.stderr` with `io.TextIOWrapper` using UTF-8 encoding
3. Uses `errors="replace"` to handle any remaining encoding issues gracefully

Also set `force_terminal=True` in the Console instance to ensure Rich output works correctly on Windows.

## Verification

```bash
$ tasker init . --yes --project-name "test" --mode api
# Successfully completes without UnicodeEncodeError
```
