# Issue #390: httpx INFO logging interleaved in CLI stdout/stderr output

## Description
Every CLI command that makes HTTP API calls (all commands when in `api` mode) emits httpx INFO-level log lines directly to the terminal. In PowerShell, these are treated as errors and displayed in red, making the CLI hard to read.

## Root Cause
httpx uses its own logger (`httpx`) at INFO level by default, which emits a log line for every HTTP request/response. No handler suppressed this for CLI usage.

## Fix
Added `logging.getLogger("httpx").setLevel(logging.WARNING)` in `ApiHttpClient.__init__` to suppress httpx INFO-level logs whenever the API client is instantiated. The API client is only used in CLI mode, so server-side logging is unaffected.

Follows the same pattern already used for `neo4j.notifications` in `neo4j_driver.py`.

## Files Changed
- `src/socialseed_tasker/infrastructure/http/api_client.py:44` — suppress httpx INFO logging

## Verification
- `tasker status` output is now clean (no more interleaved `{"timestamp":...,"logger":"httpx","message":"HTTP Request: GET..."}` lines)
- All 800+ unit tests pass

## Status: DONE
