# Issue #365: Duplicate issue detection is ambiguous

## Description
When creating an issue with a title that already exists in the same component, the CLI shows a warning but still formats the output as if the creation was successful. The warning says "Issue with title 'X' already exists in this component. Existing IDs: [uuid]" but the result table displays the issue as newly created. This ambiguity makes it unclear whether the operation was a no-op or a duplicate return.

## Expected Behavior
Either:
- Reject duplicates with a clear error and non-zero exit code, or
- Explicitly state "Using existing issue: [ID]" in the result output (not formatted as a new creation)

## Actual Behavior
Warning is shown but the output format is identical to a successful creation, making it ambiguous.

## Steps to Reproduce
1. `tasker issue create "Test" --component <id>`
2. `tasker issue create "Test" --component <id>` (same title)
3. Observe warning + success-format output

## Status: PENDING

## Priority: LOW

## Component
CLI

## Suggested Fix
Make duplicate detection explicit: change the output format when a duplicate is detected to clearly indicate no new issue was created, and optionally return a non-zero exit code.

## Impact
Low. Minor UX issue that could cause confusion during scripted issue creation.
