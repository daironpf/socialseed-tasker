# Issue #177 - API Key Header Format Inconsistency

## Description

API requires `X-API-Key` header but documentation and CLI default to `Authorization: Bearer` format. This inconsistency causes confusion for users and agents.

## Expected Behavior

The API should accept a single, documented header format for authentication. All examples and documentation should use the same format.

## Actual Behavior

```bash
# Using Authorization: Bearer (documented format) - FAILS
curl -X POST http://localhost:8000/api/v1/components \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-token" \
  -d '{"name":"test","description":"test","project":"test"}'
# Response: {"error":{"code":"UNAUTHORIZED","message":"Invalid or missing API key"}}

# Using X-API-Key (undocumented format) - WORKS
curl -X POST http://localhost:8000/api/v1/components \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-token" \
  -d '{"name":"test","description":"test","project":"test"}'
# Response: {"data":{"id":"...","name":"test",...}}
```

## Steps to Reproduce

1. Start the API with `TASKER_AUTH_ENABLED=true` and `TASKER_API_KEY=test-token`
2. Try to authenticate using `Authorization: Bearer test-token`
3. Observe authentication fails

## Root Cause

The authentication middleware only checks for `X-API-Key` header, but:
- API_REFERENCE.md documents `Authorization: Bearer` format
- CLI uses `Authorization: Bearer` when sending requests
- No validation supports both formats

## Affected Files

- `src/socialseed_tasker/entrypoints/web_api/` - authentication middleware
- `API_REFERENCE.md` - documentation (may need updating)
- `src/socialseed_tasker/entrypoints/terminal_cli/` - CLI API client

## Suggested Fix

Option 1: Standardize on `Authorization: Bearer` format (recommended):
- Update middleware to check for `Authorization: Bearer <token>`
- Update all internal API calls to use this format
- Update documentation to reflect this

Option 2: Support both formats:
- Update middleware to accept both `X-API-Key` and `Authorization: Bearer`
- This maintains backwards compatibility but adds complexity

## Impact

Users and agents must discover the correct header through trial and error. This creates friction and reduces DX score.

## Implementation

Updated 3 locations to support both `X-API-Key` and `Authorization: Bearer <token>`:

1. **app.py** (main middleware):
   ```python
   provided_key = request.headers.get("X-API-Key")
   if provided_key is None:
       auth_header = request.headers.get("Authorization", "")
       if auth_header.startswith("Bearer "):
           provided_key = auth_header[7:]
   ```

2. **routes.py** (webhook endpoint):
   ```python
   auth_header = request.headers.get("X-API-Key", "")
   if not auth_header:
       auth_header = request.headers.get("Authorization", "")
       if auth_header.startswith("Bearer "):
           auth_header = auth_header[7:]
   ```

3. **routes.py** (admin reset endpoint):
   ```python
   provided_key = request.headers.get("X-API-Key")
   if provided_key is None:
       auth_header = request.headers.get("Authorization", "")
       if auth_header.startswith("Bearer "):
           provided_key = auth_header[7:]
   ```

4. **task_skill.py** (agent skill template):
   Updated to use `Authorization: Bearer {TASKER_API_KEY}` as the preferred format.

## Status: COMPLETED