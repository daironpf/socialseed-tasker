# Issue #10: Flexible Initialization Options

## Description
The `tasker init` command should offer options for in-place scaffolding without creating the `tasker/` subfolder, providing more flexibility for different project structures.

## Expected Behavior
Add flags to control initialization location and structure, allowing:
- In-place initialization in current directory
- Custom subdirectory naming
- Default behavior preservation for backward compatibility

## Actual Behavior
The command always creates a `tasker/` subdirectory, which may not fit all project structures.

## Steps to Reproduce
1. Navigate to a project root directory
2. Run `tasker init`
3. Observe creation of `tasker/` subdirectory
4. If user wants in-place initialization, must manually restructure

## Status: DONE ✓

## Priority: LOW

## Resolution
- Already implemented in #153: Add `--inplace` / `-i` flag
- Default creates tasker/ subdirectory (backward compatible)
- This issue is duplicate of #153