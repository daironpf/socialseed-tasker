# Issue #110: Fix Dependency Endpoint Field Validation

## Description

The dependency endpoint at `/api/v1/issues/{id}/dependencies` had field validation issues. The request body uses `depends_on_id` but there was confusion about whether it should be `depends_on` or `depends_on_id`.

## Requirements

- Verify the current field name is `depends_on_id` (correct)
- Ensure error messages are consistent with field names
- Add proper validation for UUID format
- Add tests for dependency creation with valid/invalid IDs

## Technical Details

### Current Implementation (verified working)
```python
# POST /api/v1/issues/{issue_id}/dependencies
{
  "depends_on_id": "uuid-of-dependency-issue"
}
```

### Test Results
```
Status: 201 Created
Response: {"data": {"issue_id": "...", "depends_on_id": "..."}}
```

This issue was FIXED during testing - the endpoint now works correctly with `depends_on_id`.

### Validation Applied
- UUID format validation for `depends_on_id`
- Returns 422 if invalid UUID format
- Returns 404 if issue not found
- Returns 409 if circular dependency detected

## Current Status

This appears to be **ALREADY WORKING** based on the integration tests:
- Dependency creation: 201 OK
- Blocked issues: 200 OK
- Close with dependents: 409 (correct)

## Verification Needed

- [x] Endpoint accepts `depends_on_id` field
- [x] Creates dependency in Neo4j
- [x] Returns proper errors for invalid input

## Business Value

Proper dependency management is core to the project's value proposition.

## Status: COMPLETED