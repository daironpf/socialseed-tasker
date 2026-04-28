# Issue #205: Component Creation API - Missing Field Documentation

## Description

When creating a component via POST /api/v1/components, the API requires a "project" field that is not documented in the API schema or mentioned in `--help` output. This forces developers to guess required fields, slowing onboarding and creating friction.

## Problem

The API returns an error requiring an undocumented field:
```
Request: POST /api/v1/components {"name": "personal_tasks", "description": "..."}

Error: {"detail":[{"type":"missing","loc":["body","project"],"msg":"Field required"...}]}
```

The "project" field is required but:
- Not shown in OpenAPI schema at /docs
- Not mentioned in `tasker component create --help`
- Not documented in API_REFERENCE.md
- No default value provided

## Expected Behavior

All required fields should be either:
1. Documented in API schema and reference documentation
2. Have sensible defaults (e.g., "default" project)
3. Be clearly indicated in error messages (currently shows but unclear)

## Steps to Reproduce

```bash
# Try to create component without project field
curl -X POST "http://localhost:8000/api/v1/components" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-component", "description": "Test"}'

# Returns: 422 error requiring "project" field
# No documentation explains this
```

## Status

**TODO**

## Priority

**MEDIUM** - Impacts DX and developer onboarding

## Component

API, DOCUMENTATION

## Acceptance Criteria

- [ ] "project" field documented in API schema (OpenAPI)
- [ ] "project" field documented in API_REFERENCE.md
- [ ] CLI help shows required fields (`tasker component create --help`)
- [ ] OR: "project" has default value ("default")
- [ ] Error message clearly indicates field is required

## Suggested Fix

Option 1 (Documentation):
- Add "project" field to component schema in api.py
- Document in API_REFERENCE.md under /components endpoint
- Update CLI help output for component create command

Option 2 (Default value):
- Make "project" optional in schema with default="default"
- This aligns with existing issues that use "default" project

## Impact

- DX score degraded: api_clarity = 6/10
- Developer friction when exploring API
- Slows onboarding for new users

## Technical Notes

- Schema location: src/api/routes/components.py
- CLI command: src/cli/commands/component.py
- Current behavior: 422 validation error on missing "project"

## Related Issues

- Real-Test Evaluation FIND-001
- Issue #69: API Authentication (improved DX in past)