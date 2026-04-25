# Fix Duplicate Operation ID warning in OpenAPI

**Status**: OPEN
**Priority**: LOW
**Labels**: warning, api
**Created**: 2026-04-12

## Problem

The FastAPI server logs a warning about duplicate operation ID:

```
UserWarning: Duplicate Operation ID list_issues_api_v1_issues_get for function list_issues
```

This affects the OpenAPI spec generation and may cause issues with API documentation.

## Location

`src/socialseed_tasker/entrypoints/web_api/routes.py`

## Error Traceback

The warning appears when generating OpenAPI schema.

## Expected Behavior

Each route should have a unique operation ID in the OpenAPI spec.

## Test Command

```bash
curl -s http://localhost:8000/openapi.json | python -c "import sys,json; d=json.load(sys.stdin); print([p for p in d.get('paths',{}).keys()])"
```

## Suggestions

1. Add unique `operation_id` parameter to each route decorator
2. Example: `@issues_router.get("/issues", operation_id="list_issues")`
3. Use consistent naming convention: `{http_method}_{endpoint_path}`
4. Verify no duplicate route definitions