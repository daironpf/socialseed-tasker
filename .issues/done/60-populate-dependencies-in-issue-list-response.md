# Issue #60: Dependencies field empty in issue list endpoint response

## Description

The `GET /api/v1/issues` endpoint returns issues with `"dependencies": []` even when dependencies exist. The dependency data is correctly stored in Neo4j and accessible via the dedicated `/issues/{id}/dependencies` endpoint, but the list endpoint does not populate the dependencies field.

## Problem Found

When listing all issues via `GET /api/v1/issues`, every issue showed:
```json
"dependencies": [],
"blocks": [],
"affects": []
```
Even though checkout-payment had 4 dependencies and admin-dashboard had 3. The dedicated endpoint `GET /api/v1/issues/{id}/dependencies` returned correct data.

## Impact

- API consumers must make N+1 requests to get full issue data with dependencies
- Frontend Kanban board cannot show dependency indicators without extra calls
- Violates the principle of returning complete issue summaries in list responses

## Suggested Fix

- Modify the issue list repository query to include dependency IDs as a sub-query
- Or add a lightweight join in the service layer to populate `dependencies` with issue IDs
- Keep `blocks` and `affects` as computed fields if too expensive for list view

## Priority

HIGH

## Labels

api, bug, performance
