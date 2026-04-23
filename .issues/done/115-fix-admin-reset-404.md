# Issue #115: Fix Admin Reset Endpoint Returning 404

## Description

The admin reset endpoint `/api/v1/admin/reset` returns 404 during API testing. According to documentation this endpoint should exist and work.

## Current Behavior
```
POST /api/v1/admin/reset
Returns: 404 Not Found
```

## Expected Behavior
```
POST /api/v1/admin/reset
Returns: 200 OK with reset confirmation
```

## Requirements

- Verify admin router is properly registered
- Fix the endpoint to work
- Add authentication for admin endpoints

## Status: COMPLETED