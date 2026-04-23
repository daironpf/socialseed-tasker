# Issue #104: Add Missing API Routes or Document as Deprecated

## Description

Several API routes that were expected to exist based on documentation or past implementation are returning 404 Not Found. These include labels, policies, agents, sync status, and admin endpoints. Either implement them properly or clearly document them as deprecated.

## Requirements

- Investigate and implement missing routes:
  - `/api/v1/labels` - Label management
  - `/api/v1/policies` - Policy management
  - `/api/v1/agents` - Agent management
  - `/api/v1/sync/status` - Sync status
  - `/api/v1/admin/reset` - Admin reset endpoint
  - `/api/v1/projects/{name}/summary` - Project summary
- For routes that are not implemented, remove from router or add deprecation notice
- Add proper error responses for non-existent routes

## Technical Details

### Missing Routes Investigation

Based on the OpenAPI schema, these routes are NOT available:
- `/api/v1/labels` - Needs implementation
- `/api/v1/policies` - Router exists, need to verify
- `/api/v1/agents` - Router exists, need to verify
- `/api/v1/sync/status` - Needs implementation
- `/api/v1/projects` - Needs implementation

Routes that return 404:
```
/api/v1/admin/reset          -> 404
/api/v1/projects/{name}/summary -> 404
```

### Current Working Routes (confirmed)
```
/api/v1/components
/api/v1/issues
/api/v1/issues/{id}
/api/v1/issues/{id}/dependencies
/api/v1/issues/{id}/close
/api/v1/analyze/impact/{id}
/api/v1/analyze/component-impact/{id}
/api/v1/blocked-issues
/api/v1/workable-issues
/api/v1/graph/dependencies
/health
```

### Solution Approach
1. For existing routers that don't work: Fix the implementation
2. For non-existent routes: Implement them or remove from router
3. Add a clear "Not Implemented" response for deprecated features

## Business Value

Complete API coverage ensures all documented features work. Missing routes cause client errors and reduce confidence in the API.

## Status: COMPLETED