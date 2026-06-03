# Issue #396: Rate limiting lacks client-side warning and Retry-After header

## Description
The API rate limiter rejects requests after approximately 32 sequential calls with HTTP 429, but does not include a `Retry-After` header in the response. Clients must guess the wait time and retry blindly. Additionally, there is no client-side warning mechanism to inform users before hitting the limit.

## Expected Behavior
1. Rate-limited responses (HTTP 429) should include a `Retry-After` header indicating seconds to wait.
2. The CLI API client should display a warning when approaching the rate limit.
3. The API client should automatically respect `Retry-After` and retry after the specified delay.

## Actual Behavior
HTTP 429 responses contain no `Retry-After` header. Clients receive a bare 429 status with no guidance on when to retry.

## Steps to Reproduce
1. Send ~35 rapid POST requests to `/api/v1/issues`
2. Observe: HTTP 429 with no `Retry-After` header

## Status: PENDING

## Priority: LOW

## Component
API (`rate_limit.py`)

## Suggested Fix
Add `Retry-After` header to the 429 response in the rate limiting middleware. Optionally implement exponential backoff in the API client.

## Impact
Minor. The rate limit is documented. Missing `Retry-After` requires clients to implement their own retry timing.

## Related Issues
- #383 (rate limiting batch issue creation - closed)

## Changes Made
[Leave empty]

## Verification
[Leave empty]
