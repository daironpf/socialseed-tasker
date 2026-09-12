# Issue #438: Fix Issue type to use IssueStatus and IssuePriority enums

## Description
The `Issue` interface used `status: string` and `priority: string` instead of the already-defined `IssueStatus` and `IssuePriority` enums. This defeated the purpose of having enums and meant zero compile-time protection against invalid values.

## Expected Behavior
- `Issue.status` is typed as `IssueStatus`
- `Issue.priority` is typed as `IssuePriority`
- `IssueCreateRequest` and `IssueUpdateRequest` also use the enums

## Status: COMPLETED

## Priority: CRITICAL

## Component
Frontend / Types

## Changes Made
1. Changed `status: string` to `status: IssueStatus` in `Issue` interface
2. Changed `priority: string` to `priority: IssuePriority` in `Issue` interface
3. Updated `IssueCreateRequest.priority` to `IssuePriority`
4. Updated `IssueUpdateRequest.priority` to `IssuePriority` and `status` to `IssueStatus`
5. Fixed `CreateIssueModal.vue` to use `IssuePriority.MEDIUM` instead of string literal

## Verification
- `npm run build` passes without TypeScript errors
- IDE now provides autocompletion for valid status/priority values
- Invalid values are caught at compile time

## Related Issues
- None
