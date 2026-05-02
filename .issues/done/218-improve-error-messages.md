# Issue #218 - Improve Error Messages with Field-Level Details

## Description

Error messages are too generic. "There was an error parsing the body" doesn't indicate which field has the problem, what format is expected, or whether it's a validation or parsing issue.

## Problem

```json
{"detail":"There was an error parsing the body"}
```

All errors return the same vague message:
- Invalid JSON
- Missing required field
- Wrong field type
- Character encoding issue

## Root Cause

The API returns a generic error without field-level details.

## Expected Behavior

Use Pydantic validation error format to show field-specific issues:

```json
{
  "detail": "Validation Error",
  "errors": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "missing"
    }
  ]
}
```

## Implementation Steps

### Step 1: Review FastAPI exception handling

Check `routes.py` for custom exception handlers.

### Step 2: Update error responses

Return detailed validation errors from Pydantic.

## Affected Files

- `src/socialseed_tasker/entrypoints/web_api/routes.py`

## Priority

HIGH

## Status: COMPLETED