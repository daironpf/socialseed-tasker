# Issue #125: Document API Pagination Format

## Description

Document the pagination format used by the API to help client developers.

## Current State

- API uses paginated responses
- Format: `{data: {items: [], pagination: {}}}`
- Not documented in OpenAPI schema

## Problem

Client developers need to know:
- Page number starts at 1
- Default limit is 20
- Maximum limit is 100

## Requirements

1. Document pagination in OpenAPI
2. Add examples to documentation
3. Document response format

## Documentation Format

```json
{
  "data": {
    "items": [...],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 100,
      "has_next": true,
      "has_prev": false
    }
  }
}
```

## Implementation

```python
# Improve OpenAPI schema
class PaginationMeta(BaseModel):
    page: int = Field(..., description="Current page number (starts at 1)")
    limit: int = Field(..., description="Items per page (default: 20, max: 100)")
    total: int = Field(..., description="Total items available")
    has_next: bool = Field(..., description="Whether more pages exist")
    has_prev: bool = Field(..., description="Whether previous page exists")
```

## Status: COMPLETED