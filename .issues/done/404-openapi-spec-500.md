# Issue #404: OpenAPI spec returns 500 at /openapi.json

## Description
`GET /openapi.json` returns HTTP 500 Internal Server Error. FastAPI schema generation fails, likely due to a model with circular references or an unsupported type annotation. This blocks API discovery tools and client generation.

## Expected Behavior
`GET /openapi.json` should return a valid OpenAPI 3.0 schema describing all available endpoints.

## Actual Behavior
```json
{
  "detail": "Internal Server Error"
}
```
HTTP 500 with no additional detail.

## Steps to Reproduce
1. Start Tasker services: `cd .agent/tasker && docker compose up -d`
2. `curl http://localhost:8888/openapi.json`
3. Observe 500 error

## Status: COMPLETED

## Priority: CRITICAL

## Component
API / OpenAPI Schema

## Suggested Fix
Locate the Pydantic/FastAPI model causing the schema generation failure. Common causes: circular references in `APIResponse` generic types, missing `model_config`, or custom types without JSON schema. Add `model_config = {"arbitrary_types_allowed": True}` where needed or use `response_model_exclude_unset=True`.

## Impact
- Blocks API discovery via Swagger UI at `/docs`
- Prevents OpenAPI-based code generation
- Hinders third-party integration
