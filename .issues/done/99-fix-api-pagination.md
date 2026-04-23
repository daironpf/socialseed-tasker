# Issue #99: Fix API Pagination Format Inconsistency

## Description

The API returns paginated responses in an inconsistent format across different endpoints. Some endpoints return `{data: {items: [...]}}` while others return `{data: [...]}`. This causes client code to fail when expecting a specific format.

## Requirements

- Standardize pagination format across ALL API endpoints
- Ensure consistent response structure for both single items and lists
- Maintain backward compatibility with existing clients
- Document the response format in OpenAPI schema

## Technical Details

### Current Response Formats

**Paginated list (current):**
```json
{
  "data": {
    "items": [...],
    "total": 20,
    "page": 1,
    "page_size": 50
  },
  "error": null,
  "meta": {...}
}
```

**Single item (current):**
```json
{
  "data": {
    "id": "uuid",
    "title": "...",
    ...
  },
  "error": null,
  "meta": {...}
}
```

### Problem
When client code expects `{data: [...]}` (array directly in data), it fails because actual format is `{data: {items: [...]}}`.

### Affected Endpoints
- GET /api/v1/components
- GET /api/v1/issues
- GET /api/v1/dependencies (if exists)
- Any paginated endpoint

### Solution Approach
Option 1: Standardize on `{data: {items: [...]}}` for all list responses
Option 2: Add a "format" query parameter to switch between formats
Option 3: Add a compatibility layer that detects client expectation

**Recommended:** Option 1 - Standardize on `{data: {items: [...]}}` format and update all clients.

## Business Value

Consistent API responses prevent client errors and make integration easier. Clients can confidently parse responses knowing the format.

## Status: COMPLETED