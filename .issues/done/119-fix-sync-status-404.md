# Issue #119: Fix Sync Status Endpoint Returns 404

## Description

The sync status endpoint at `/api/v1/sync/status` returns 404 Not Found in the running Docker container.

## Current Behavior
```
GET /api/v1/sync/status
Status: 404 Not Found
```

## Expected Behavior
```
GET /api/v1/sync/status
Status: 200 OK
{
  "status": "online/offline",
  "queue_size": 0
}
```

## Root Cause

The sync router may not be registered correctly in the running container. Routes exist in routes.py but may not be included.

## Verification Required

- Check if sync_router is included in app.py
- Verify route path: `/api/v1/sync/status`
- Check if running container has the route registered
- Rebuild Docker image if needed

## Status: COMPLETED