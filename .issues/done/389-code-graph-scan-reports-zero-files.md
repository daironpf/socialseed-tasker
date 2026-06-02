# Issue #389: `tasker code-graph scan . --incremental` reports 0 files, 0 symbols

## Description
Running `tasker code-graph scan . --incremental` from the project root returns "Found 0 files, 0 symbols, 0 imports", even though the directory contains hundreds of Python source files.

## Root Cause
On Windows, `os.walk` returns paths with backslashes (`.\src\...\file.py`), while `git diff --name-only HEAD` returns paths with forward slashes (`src/.../file.py`). The incremental filter compared `str(file_path) not in modified_files`, which always failed because of the path format mismatch. With any unstaged changes in the working tree, `modified_files` would be a non-empty set, causing ALL files to be filtered out.

## Fix
`code_parser.py:111` — changed `str(file_path) not in modified_files` to `file_path.as_posix() not in modified_files`. The `.as_posix()` method converts backslashes to forward slashes on all platforms, matching the git output format.

## Files Changed
- `src/socialseed_tasker/infrastructure/code_parser.py:111` — path normalization for cross-platform compatibility

## Verification
- `tasker code-graph scan . --incremental`: "Found 2 files, 30 symbols, 27 imports" (was 0 before fix)
- `tasker code-graph scan .`: "Found 390 files, 3561 symbols, 2394 imports"
- All 800+ unit tests pass (63 code-graph specific tests)

## Status: DONE
