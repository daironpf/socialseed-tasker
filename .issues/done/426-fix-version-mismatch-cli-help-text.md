# Issue #426: Fix version mismatch in CLI help text

## Description
The `tasker --help` output references "New in v1.1.0" for the `dependency add-batch` command, but the system version is v1.0.2. This creates confusion about what features are available.

## Expected Behavior
CLI help text should reference the current version or use a more generic description like "New feature".

## Actual Behavior
`tasker --help` shows: "New in v1.1.0: Use 'tasker dependency add-batch' for bulk operations without rate-limit retries."

## Steps to Reproduce
1. Run `tasker --help`
2. Note the "New in v1.1.0" reference while system reports v1.0.2

## Status: COMPLETED

## Priority: LOW

## Component
CLI

## Suggested Fix
Either update the version reference or change to "New: Use 'tasker dependency add-batch'..." in `src/socialseed_tasker/cli/app.py` line 124.

## Impact
Minor documentation inconsistency; doesn't affect functionality.

## Related Issues
(none)

## Changes Made
Changed "New in v1.1.0" to "Tip:" in `src/socialseed_tasker/cli/app.py:124` to avoid version-reference confusion. Now reads: "Tip: Use 'tasker dependency add-batch' for bulk operations without rate-limit retries."

## Verification
- 810 project unit tests pass
- `tasker --help` shows correct text without version reference
