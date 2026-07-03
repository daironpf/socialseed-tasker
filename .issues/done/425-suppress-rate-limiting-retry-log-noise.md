# Issue #425: Suppress rate limiting retry log noise

## Description
The CLI produces verbose `[INFO] Rate limited (attempt 1/3). Retrying in 1.3s...` messages during normal operation when the rate limiter triggers. These messages are at `logger.info` level and clutter the output.

## Expected Behavior
Rate limiting retry messages should only appear in debug/verbose mode, not during normal CLI usage.

## Actual Behavior
Every rate-limited API call prints `[INFO] Rate limited (attempt %d/%d). Retrying in %.1fs...` to stdout.

## Steps to Reproduce
1. Run `tasker dependency add` multiple times in quick succession
2. Observe rate limit messages interleaved with normal output

## Status: COMPLETED

## Priority: LOW

## Component
CLI / infrastructure/http/api_client.py

## Suggested Fix
Change `logger.info` to `logger.debug` on line 95 of `src/socialseed_tasker/infrastructure/http/api_client.py`

## Impact
Cleaner CLI output for normal users; rate limit info still visible with `--verbose`

## Related Issues
(none)

## Changes Made
Changed `logger.info` to `logger.debug` in `src/socialseed_tasker/infrastructure/http/api_client.py:95` to suppress rate limiting retry messages from normal CLI output. They now only appear with `--verbose`.

## Verification
- 810 project unit tests pass
- 31 e-commerce tests pass
- Rate limiting retry messages no longer pollute normal CLI output
