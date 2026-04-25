# Fix Sync router returning 404 Not Found

**Status**: OPEN
**Priority**: MEDIUM
**Labels**: bug, api
**Created**: 2026-04-12

## Problem

The sync router is defined in `routes.py` but all its endpoints return 404 Not Found.

Endpoints affected:
- `/api/v1/sync/status` - GET
- `/api/v1/sync/queue` - GET
- `/api/v1/sync/force` - POST

## Location

`src/socialseed_tasker/entrypoints/web_api/routes.py:2350-2407`
`src/socialseed_tasker/entrypoints/web_api/app.py:207,194`

## Expected Behavior

The sync endpoints should work and return sync status/queue/force results.

## Test Commands

```bash
curl -s "http://localhost:8000/api/v1/sync/status"
curl -s "http://localhost:8000/api/v1/sync/queue"
```

## Current Behavior

```json
{"detail":"Not Found"}
```

## Suggestions

1. Verify `sync_router` is properly imported in app.py
2. Check router registration order
3. Verify the router is included in the correct prefix
4. Add debug logging to trace route registration