# Issue #116: Standardize Pagination Format

## Description

The API uses inconsistent pagination formats across different endpoints. Some return `{data: {items: [...]}}` while others return different structures.

## Current Behavior
Different pagination formats in various endpoints.

## Expected Behavior
Standardize format across all endpoints:
```json
{
  "data": {
    "items": [...],
    "total": 20,
    "page": 1,
    "page_size": 50
  }
}
```

## Requirements

- Audit all list endpoints for pagination
- Standardize response format
- Document pagination format in OpenAPI

## Status: COMPLETED