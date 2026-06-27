# Issue #399: Silent loss of issues during bulk API operations

## Description

During bulk creation of 50 issues via API at 100ms intervals, 7 issues were silently rejected by rate limiting. The calling script reported success for all 50 because it only checked for `data.id` presence (not HTTP status code). The API correctly returned 429 but the client did not handle it.

## Expected Behavior
Client should properly handle 429 errors and retry, or inform the user of the actual number of created issues.

## Actual Behavior
7 out of 50 requests returned 429 and were silently dropped. Script reported "Created 50 issues" when only 43 were created.

## Steps to Reproduce
1. Send 50 POST requests to `/api/v1/issues` with <200ms intervals
2. Verify actual count vs expected count
3. Observe discrepancy

## Status: PENDING

## Priority: LOW

## Component
API / Client Libraries

## Suggested Fix
1. Add batch endpoint (see #397)
2. Document that API has ~20 burst / ~2 per sec rate limits
3. Improve client-side retry logic

## Impact
Data integrity risk during bulk operations if clients don't handle 429 properly.

## Related Issues
- #397 (Rate limiting silent failures)
