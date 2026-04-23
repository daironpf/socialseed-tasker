# Fix API component-impact to accept short IDs

**Status**: COMPLETED
**Priority**: MEDIUM
**Labels**: bug, api
**Created**: 2026-04-12

## Problem

The API endpoint `/api/v1/analyze/component-impact/{id}` doesn't accept short IDs like other endpoints.

## Location

`src/socialseed_tasker/entrypoints/web_api/routes.py`

## Expected Behavior

```bash
curl "http://localhost:8000/api/v1/analyze/component-impact/1fa8d747"
```

## Current Behavior

```
{"error":{"code":"VALIDATION_ERROR","message":"badly formed hexadecimal UUID string"}}
```

## Test Commands

```bash
# These should all work:
curl "http://localhost:8000/api/v1/analyze/component-impact/1fa8d747"
curl "http://localhost:8000/api/v1/analyze/component-impact/1fa8d747-46bc-4034-9400-442c93a0832b"
curl "http://localhost:8000/api/v1/analyze/component-impact/backend"
```

## Suggestions

1. Add path parameter validation similar to CLI's `resolve_component_id`
2. Support full UUID, short ID (8+ chars), and name lookup