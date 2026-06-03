# Issue #392: Missing doc-sync CLI command

## Description
The installed version of SocialSeed Tasker does not include a `tasker doc-sync` command. Documentation synchronization must be performed manually or via external tooling.

## Expected Behavior
A `tasker doc-sync` command should exist (and appear in `tasker --help`) that scans project documentation, links documentation files to the relevant issues and components in the graph, and reports on documentation coverage.

## Actual Behavior
`tasker doc-sync` returns: `Error: No such command 'doc-sync'`.

## Steps to Reproduce
1. Run: `tasker doc-sync`
2. Observe: `Error: No such command 'doc-sync'`

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Implement a `doc-sync` CLI command that scans `.md` files in the project, extracts issue/component references, and creates graph relationships for documentation coverage tracking.

## Impact
Minor. Documentation synchronization can still be performed manually. The graph-based approach would enhance traceability.

## Related Issues
- (none)

## Changes Made
[Leave empty]

## Verification
[Leave empty]
