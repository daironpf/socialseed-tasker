# Issue #358: `tasker issue list -s CLOSED` shows all issues instead of only closed

## Description
The `-s` (status) filter for `issue list` does not work correctly. It returns all issues regardless of the specified status value.

## Expected Behavior
`tasker issue list -s CLOSED` should show only closed issues.

## Actual Behavior
Shows all 50 issues including OPEN ones.

## Steps to Reproduce
1. Have both OPEN and CLOSED issues
2. Run `tasker issue list -s CLOSED`
3. List includes OPEN issues

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Fix the Cypher query to properly filter by status when the `-s` flag is provided.

## Impact
Users cannot effectively filter issues by status from the CLI.
