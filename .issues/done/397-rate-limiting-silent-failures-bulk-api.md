# Issue #397: Rate limiting causes silent failures on bulk API operations

## Description

When creating issues via REST API with rapid intervals, the rate limiter triggers after ~20 requests and returns 429 errors. The error message is clear (`rate_limited`, `retry_after: 1`), but there's no batch endpoint for creating multiple issues at once.

## Expected Behavior

Bulk operations should either:
- Have a dedicated batch endpoint
- Or the error handling should be more prominent

## Actual Behavior

Rate limiting kicks in after ~20 burst requests (then ~1/sec). Error response is structured but requires manual retry logic.

## Steps to Reproduce

1. POST requests to `/api/v1/issues` faster than 20 per burst
2. Observe 429 responses with `{"status":"error","error":"rate_limited","retry_after":1}`

## Status: PENDING

## Priority: MEDIUM

## Component
API

## Suggested Fix
Add a `POST /api/v1/issues/batch` endpoint for bulk creation, or document burst limits more prominently in API responses.

## Impact
Slows down bulk operations; agents must add manual delays; data integrity risk during bulk operations.

## Related Issues
- #399 (Silent loss of issues)
