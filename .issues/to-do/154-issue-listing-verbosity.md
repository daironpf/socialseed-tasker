# Issue #05: Issue Listing Verbosity Enhancement

## Description
`tasker issue list` does not show issue titles by default, only IDs, status, and priority. It's hard to identify issues without titles in a terminal view.

## Expected Behavior
Include the Title (truncated if necessary) in the default table view so users can identify issues at a glance.

## Actual Behavior
The default table only shows ID, Status, Priority, and Component columns - titles are not displayed.

## Steps to Reproduce
1. Create several issues with different titles
2. Run `tasker issue list`
3. Observe that titles are not shown in the output table

## Status: PENDING

## Priority: MEDIUM

## Recommendations
- Add Title column (truncated to 30-40 characters) to default table view
- Keep backward compatibility - titles could be shown in `--json` output already
- Consider adding `--verbose` flag to show full titles when needed
- Ensure table remains readable with the additional column
- Update any documentation showing the default output format