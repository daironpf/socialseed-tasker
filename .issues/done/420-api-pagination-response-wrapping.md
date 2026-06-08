# Issue #420: API pagination response wraps issues in nested data.items

## Description
The API endpoint `GET /api/v1/issues` returns issues wrapped in `data.items` array instead of a flat `data` array. The pagination metadata is in `data.pagination`. This is inconsistent with other endpoints that return `data` as a direct array.

## Expected Behavior
API response format should be consistent across all list endpoints — either all use `data` as direct array or all use `data.items` with `data.pagination`.

## Actual Behavior
`GET /api/v1/issues` returns:
```json
{"data": {"items": [...], "pagination": {...}}, "meta": {...}}
```
While simpler endpoints return:
```json
{"data": [...], "meta": {...}}
```

## Steps to Reproduce
1. `curl http://localhost:8888/api/v1/issues`
2. Observe nested `data.items` structure instead of flat `data` array

## Status: COMPLETED

## Priority: LOW

## Component
API

## Suggested Fix
Flatten paginated responses: `data` is now a direct array, pagination metadata moved to `meta.pagination`.

## Impact
Low. Consumer needs to handle nested structure for paginated endpoints only. Not a functional bug.

## Related Issues
- (none)

## Changes Made
- Modified `Meta` schema in `schemas.py` to include optional `pagination: PaginationMeta` field
- Updated `list_issues` (`issues.py:354`) to return flat `data` array + `meta.pagination`
- Updated `list_components` (`components.py:196`) to return flat `data` array + `meta.pagination`
- Updated `list_dependencies` (`dependencies.py:280`) to return flat `data` array + `meta.pagination`
- Updated all tests in `test_api.py` and `test_api_routes_coverage.py` to use new flat format

## Verification
All 24 pagination/component/dependency tests pass in both `test_api.py` and `test_api_routes_coverage.py`.
