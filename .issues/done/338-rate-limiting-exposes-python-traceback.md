# Issue #338: Rate limiting returns raw Python traceback to user

## Description
When rate limited (HTTP 429), the CLI shows a full Python traceback instead of a clean user-friendly error message. This exposes internal code paths.

## Expected Behavior
CLI should display a clean, user-friendly error message when rate limited.

## Actual Behavior
Full Python traceback is shown including internal file paths and call stack.

## Steps to Reproduce
1. Run multiple `tasker dependency add` commands rapidly
2. Observe full traceback on 429 response

## Status: PENDING

## Priority: HIGH

## Component
CLI

## Suggested Fix
Catch `RemoteServiceError` in CLI handlers and display only the structured error message, not the full traceback

## Impact
Poor DX for end users; exposes internal infrastructure details

## Related Issues
-
