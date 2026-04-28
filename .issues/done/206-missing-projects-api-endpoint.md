# Issue #206: Missing Projects API Endpoint

## Description

When exploring the API to find valid project names, developers cannot query the list of existing projects. The expected endpoint GET /api/v1/projects returns 404, making it impossible to discover valid project values for component/issue creation.

## Problem

Attempted to list projects via API:
```bash
# Request: GET /api/v1/projects
# Response: 404 Not Found
```

This prevents:
1. Discovering existing project names
2. Programmatic project enumeration
3.Validating project names before creating components
4. DX exploration without reading documentation

## Expected Behavior

There should be an endpoint to list all projects:
- GET /api/v1/projects - List all projects
- Response: {"data": {"items": [...]}}

Or alternatively:
- Document where to find valid project names
- Provide default project name in all examples

## Steps to Reproduce

```bash
# Try to list projects
curl http://localhost:8000/api/v1/projects

# Returns: 404 Not Found

# Try to discover valid project values
curl http://localhost:8000/api/v1/components?project=<what-goes-here?>
# Must guess valid project name
```

## Status

**TODO**

## Priority

**LOW** - Minor DX friction

## Component

API, DOCUMENTATION

## Acceptance Criteria

- [ ] GET /api/v1/projects endpoint exists and returns project list
- [ ] OR: Document valid project values in API_REFERENCE.md
- [ ] OR: Default project value clearly indicated in examples

## Suggested Fix

Option 1 (Add endpoint):
- Create GET /api/v1/projects in api.py
- Query all distinct projects from Neo4j
- Return in paginated format

Option 2 (Documentation):
- Document "default" as the default project in API_REFERENCE.md
- Add example showing project field usage

## Impact

- DX score degraded: api_clarity = 6/10
- Minor friction when exploring API
- Forces users to read documentation instead of discoverability

## Technical Notes

- No projects endpoint currently exists
- Default project appears to be "default" (from testing)
- Graph schema may have Project nodes

## Related Issues

- Real-Test Evaluation FIND-002
- Issue #205: Component Creation API - Missing Field Documentation (same root cause)