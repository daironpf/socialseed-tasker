# Issue #274: Workable Issues Endpoint 500 Error

## Description
The `/api/v1/workable-issues` endpoint throws an internal server error (500) when called, preventing users from seeing issues ready to work on.

## Expected Behavior
The endpoint should return a list of issues that have no open dependencies (workable issues).

## Actual Behavior
Returns: `{"data":null,"error":{"code":"INTERNAL_ERROR","message":"An unexpected error occurred"}}`

## Steps to Reproduce
1. Start the API server
2. Call GET http://localhost:8000/api/v1/workable-issues
3. Observe 500 error response

## Status: COMPLETED

## Priority: HIGH

## Component
API

## Suggested Fix
Check the implementation of workable-issues in routes.py for missing edge case handling or null reference. Add proper error handling and logging to diagnose the root cause.

## Impact
Users cannot view issues that are ready to be worked on, blocking the main use case of the system.

## Related Issues
- Related to issue #65 (Workable Issues feature)