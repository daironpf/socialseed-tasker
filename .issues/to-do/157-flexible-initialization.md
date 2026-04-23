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

## Status: PENDING

## Priority: LOW

## Recommendations
- Add `--inplace` or `-i` flag for in-place initialization
- Add `--subdirectory` or `-d` flag to specify custom subdirectory name
- Maintain default `tasker/` subdirectory behavior
- Update documentation with usage examples for each option
- Ensure all initialization features work with both modes
- Add validation to prevent directory conflicts