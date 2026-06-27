# Issue #419: Improve reasoning endpoint response format

## Description
POST `/api/v1/issues/{id}/reasoning` returns the full issue object instead of a simple confirmation. This is overly verbose for a logging endpoint and increases response payload unnecessarily.

## Expected Behavior
The endpoint should return a lightweight confirmation like `{"status": "ok", "message": "Reasoning logged", "reasoning_id": "..."}`.

## Actual Behavior
Returns the complete issue object including all fields (id, title, description, status, priority, labels, timestamps, etc.).

## Steps to Reproduce
1. POST to `http://localhost:8888/api/v1/issues/{id}/reasoning` with JSON body
2. Observe that the response is the full issue object

## Status: PENDING

## Priority: MEDIUM

## Component
API

## Suggested Fix
Modify the `/api/v1/issues/{id}/reasoning` endpoint to return a confirmation response instead of the full issue object.

## Impact
Medium. Increases bandwidth usage and response parsing complexity for API consumers (especially AI agents making frequent reasoning logs).

## Related Issues
- (none)

## Changes Made
[Leave empty]

## Verification
[Leave empty]
