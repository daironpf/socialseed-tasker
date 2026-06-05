# Issue #408: Pagination default limit of 20 may hide data from callers

## Description
`GET /api/v1/issues` without a `limit` parameter defaults to 20 items per page. Callers unaware of pagination may believe the system has only 20 issues, when many more exist. The `pagination` block is included in the response but may be overlooked.

## Expected Behavior
- Document the default pagination limit clearly in the API response or OpenAPI spec.
- Alternatively, raise the default limit to a more practical value (e.g., 50 or 100).
- The `pagination` meta should be more prominent in client-facing documentation.

## Actual Behavior
First page returns 20 items regardless of total count. Unpaginated clients see only 20 issues.

## Steps to Reproduce
1. Create 50+ issues
2. `curl http://localhost:8888/api/v1/issues`
3. Observe only 20 items returned

## Status: PENDING

## Priority: LOW

## Component
API / Issues / Pagination

## Suggested Fix
- Update default `limit` from 20 to 50.
- Ensure the `pagination` block is prominently documented.
- Add a `Link` header for HATEOAS-style pagination navigation.

## Impact
- Client confusion: "I created 50 issues but only see 20."
- Requires clients to implement pagination logic.
