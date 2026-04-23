# Issue #04: Project Initialization Location Control

## Description
The `init` command scaffolds a useful structure for external projects but creates a `tasker/` subdirectory inside the target. If a user is already in a `tasker/` folder or wants it in the root, it might be redundant.

## Expected Behavior
Add a flag to initialize in-place (without creating the `tasker/` subfolder) or let users control the output directory structure.

## Actual Behavior
The command always creates a `tasker/` subdirectory, which may be redundant depending on the user's current location.

## Steps to Reproduce
1. Navigate to a project root directory
2. Run `tasker init .`
3. Observe that it creates `./tasker/` subdirectory instead of initializing in current directory

## Status: PENDING

## Priority: LOW

## Recommendations
- Add `--inplace` or `--no-subdir` flag to initialize without creating subdirectory
- Keep default behavior for backward compatibility
- Allow users to specify custom output path
- Update documentation to explain the flag usage