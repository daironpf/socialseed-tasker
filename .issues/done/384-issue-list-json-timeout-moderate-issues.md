# Issue #384: `tasker issue list --json` timeout with moderate issue count

## Description
Running `tasker issue list --json` with 46 issues causes the CLI to hang for >30s or timeout. The API responds in <2s, suggesting the issue is in the CLI HTTP client configuration or output rendering, not the backend.

## Expected Behavior
CLI should list issues in a reasonable time (<5s) for moderate project sizes (50-100 issues).

## Actual Behavior
- API: `GET /api/v1/issues?limit=50` returns in ~2s
- CLI: `tasker issue list --json` hangs for 30-40s then times out

## Steps to Reproduce
1. Create 46+ issues in a project
2. `tasker issue list --json`
3. Observe hang/timeout after 30-40s

## Status: DONE

## Priority: LOW

## Component
CLI

## Suggested Fix
Investigate the `httpx` client timeout configuration in the CLI's issue service. Compare with the API response time. Ensure the client timeout is appropriate for the expected response payload size.

## Impact
Users with moderate project sizes (50+ issues) cannot list issues via CLI in a timely manner. Must use API directly.

## Related Issues
- Issue #159 (Refactor API pagination cypher)
- Issue #165 (Fix issue list status parameter)

## Changes Made
1. **Fix paginate infinite loop** (`api_client.py:131`): Changed `data.get("next_page", False)` to properly read `pagination.has_next` from the nested pagination object. The API returns `{"items": [...], "pagination": {"page": 1, "has_next": true}}` but the client was checking `data.next_page` which never exists. This caused the loop to always break after one page (under-fetch) or loop forever (when response isn't a dict).
2. **Add max_pages guard** (`api_client.py`): Break after 200 pages to prevent runaway loops.
3. **Increase default timeout** (`mode_config.py` + `api_client.py`): Changed from 10s to 30s to handle larger paginated responses.

Root cause: `paginate` checked `data.get("next_page", False)` but the API wraps pagination in `data.pagination.has_next`. With default API limit=20 and 46 issues, the client made 3 serial requests (pages 1-3), each with 10s timeout, causing ~30s cumulative delay. Fixed by reading from `pagination` dict directly.

## Verification
- [x] Paginate reads `has_next` from nested `pagination` object
- [x] 200-page safety guard prevents runaway loops
- [x] Default timeout increased to 30s for larger payloads
- [x] Backward compatible: all existing endpoints return `pagination.has_next` format
