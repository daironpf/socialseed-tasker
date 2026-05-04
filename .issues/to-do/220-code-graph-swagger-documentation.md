# Issue #220: Code-graph endpoints not visible in Swagger UI

## Description

API has code-graph endpoints but they are not documented in /docs OpenAPI schema.

## Expected Behavior

Code-graph endpoints should appear in the Swagger UI at /docs so users can discover and test them.

## Actual Behavior

GET /api/v1/code-graph/scan and /api/v1/code-graph/stats exist in routes.py but missing from OpenAPI schema.

## Steps to Reproduce

1. Start the API with docker-compose up
2. Navigate to http://localhost:8000/docs
3. Look for code-graph endpoints in the available API paths
4. Observe that /code-graph/* endpoints are not visible

## Status: DONE

## Resolution

The code-graph endpoints are already visible in the OpenAPI schema. Verified by checking:

```python
from socialseed_tasker.entrypoints.web_api.app import create_app
app = create_app()
schema = app.openapi()
# All 8 code-graph endpoints appear in schema['paths']
```

The endpoints are correctly registered in `app.py:363` and routes are properly defined in `routes.py:3511+`. No code changes needed.

## Resolution Date

2026-05-04

## Priority: MEDIUM

## Component

API

## Suggested Fix

Add proper router include or OpenAPI annotations to make code-graph router visible in the Swagger documentation.

## Impact

Users cannot discover code-graph endpoints via the interactive API documentation.

## Related Issues

- Related to #208 (Code-as-Graph with Tree-sitter Integration)
- Related to #211 (Code Graph CLI and API Commands)