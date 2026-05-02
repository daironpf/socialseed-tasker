# Issue #217 - Fix JSON Parsing with Accented Characters

## Description

API returns generic "There was an error parsing the body" when request contains accented characters (á, é, í, ó, ú) or uses curl pipe.

## Problem

```bash
# Working
curl --data-binary '{"title":"Paciente"}' http://localhost:8000/api/v1/issues

# Failing
echo '{"title":"Paciente"}' | curl -d @- http://localhost:8000/api/v1/issues
# Returns: {"detail":"There was an error parsing the body"}
```

## Root Cause

The API doesn't properly handle non-ASCII characters or piped input.

## Expected Behavior

API should return specific validation errors showing which field or character caused the problem.

## Implementation Steps

### Step 1: Investigate JSON parsing

Check FastAPI/Starlette configuration for character encoding handling.

### Step 2: Improve error messages

Return Pydantic validation errors with field-level details.

## Affected Files

- `src/socialseed_tasker/entrypoints/web_api/routes.py`
- `src/socialseed_tasker/core/validation/`

## Priority

MEDIUM

## Status: COMPLETED