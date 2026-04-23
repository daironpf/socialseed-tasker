# Issue #39: Add test coverage for init command

## Description

The `tasker init` command lacks unit tests. While the scaffolding functionality is tested in core, the CLI integration tests for init are missing.

### Tests needed

- Test `tasker init <directory>` creates files correctly
- Test `tasker init <directory> --force` overwrites existing files
- Test `tasker init <nonexistent>` shows appropriate error
- Test that templates are loaded correctly from package assets

## Status: PENDING
