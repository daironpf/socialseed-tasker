# Issue #383: HTTP 429 rate limiting during batch issue creation

## Description
Batch issue creation (50 issues) hits HTTP 429 Too Many Requests after ~17 successful requests. The error message is clear but there is no `Retry-After` header and no guidance on optimal batch size or delay. 4 out of 50 issues (8%) failed during black-box testing.

## Expected Behavior
- 429 responses should include a `Retry-After` header
- CLI `issue create --help` should document rate limits
- Consider a `--batch-sleep` option for bulk creation scripts

## Actual Behavior
- `HTTP Request: POST http://localhost:8888/api/v1/issues "HTTP/1.1 429 Too Many Requests"`
- No `Retry-After` header
- No documentation on batch rate limits
- 4 issues silently lost during batch creation

## Steps to Reproduce
1. `for ($i=0; $i -lt 50; $i++) { tasker issue create "Issue $i" -p medium -c <component-id> }`
2. Observe 429 responses after ~17 successful requests
3. Check count: fewer than 50 issues created

## Status: DONE

## Priority: MEDIUM

## Component
API, CLI

## Suggested Fix
1. Add `Retry-After` header to 429 responses in FastAPI rate limiter middleware
2. Document rate limits in `tasker issue create --help`
3. Consider `--batch-sleep <ms>` flag for bulk creation

## Impact
Scripts and automated workflows for bulk issue creation fail unpredictably. Users must manually add delays.

## Related Issues
- #108 (Rate limiting)
- #311 (Add Rate Limiting and Abuse Protection - v1.1.0)

## Changes Made
1. **API V1 middleware** (`app.py:221`): Added `Retry-After` header calculated from window end minus current time
2. **API V2 middleware** (`rate_limit.py:40,46`): Added `Retry-After: 1` header to both user and IP 429 responses
3. **CLI doc** (`issue_commands.py:63`): Added rate limit tip to `ISSUE_CREATE_EPILOG`
4. **CLI doc** (`app.py:98`): Added rate limit note to main `APP_EPILOG`

## Verification
- [x] 429 response includes `Retry-After: <seconds>` header in V1 middleware
- [x] 429 response includes `Retry-After: 1` header in V2 middleware (both user and IP)
- [x] `tasker issue create --help` shows rate limit tip
- [x] `tasker --help` shows rate limit note in epilog
