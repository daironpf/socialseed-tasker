# Issue #201 - API Response Format Inconsistency

## Description

The API endpoints return inconsistent response structures, forcing API consumers to handle different formats depending on the endpoint called. This creates an unpredictable DX and requires custom handling logic.

## Status: COMPLETED

## Priority

**LOW** - DX improvement

## Component

API, REST, Documentation

## Changes Made

### Updated API_REFERENCE.md

Added comprehensive "Response Format Standard" section documenting:

1. **List Responses (Paginated)** - Format with items and pagination wrapper
2. **Single Item Responses** - Direct object in data field
3. **Embedded List Responses** - Lists without pagination (dependencies)
4. **Error Responses** - Error message in error field
5. **Response Fields** - Complete field reference table
6. **Pagination Fields** - Pagination metadata reference

### Clarified Dependency Endpoint

Added note to `/issues/{id}/dependencies` endpoint noting it returns embedded list without pagination.

## Verification

```bash
$ python -m ruff check src/
All checks passed!
```

## Impact

API consumers now have clear documentation of response formats:
- No need to guess response structure
- Consistent documentation across all endpoints
- Field reference tables for easy lookup

## Design Decision

After evaluating options, chose **Option B (Document the variance)**:
- List responses with pagination are appropriate for large datasets
- Embedded lists without pagination are appropriate for small related data (dependencies)
- Single item responses are direct objects

This is intentional design, not a bug. Documenting ensures consistent understanding.

## Related Issues

- Issue #125: Document pagination (related)
- Real-Test Evaluation: FIND-003