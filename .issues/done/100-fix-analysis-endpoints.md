# Issue #100: Fix Missing/404 Analysis Endpoints

## Description

Some analysis endpoints return 404 Not Found, limiting the component impact analysis capabilities. The available routes show that some endpoints exist but respond incorrectly or are missing proper implementation.

## Requirements

- Investigate why `/api/v1/analyze/component-impact/{component_id}` returns 404
- Investigate why `/api/v1/analyze/root-cause` returns 404 (may need POST)
- Add proper implementation for component impact analysis
- Ensure root cause analysis works correctly
- Add tests for all analysis endpoints

## Technical Details

### Available Analysis Routes (from OpenAPI)
```
/api/v1/analyze/component-impact/{component_id}  -> Returns 404
/api/v1/analyze/impact/{issue_id}                -> Returns 200 (working)
/api/v1/analyze/link-test                         -> Available
/api/v1/analyze/root-cause                        -> Returns 404 (expects POST?)
```

### Current Working Endpoints
- `/api/v1/analyze/impact/{issue_id}` - GET returns 200 OK

### Endpoints Needing Fix
1. **component-impact** - Should analyze all issues for a given component
2. **root-cause** - Should accept test failure data and find root causes

### Expected Functionality

**Component Impact Analysis:**
```python
# GET /api/v1/analyze/component-impact/{component_id}
{
  "component_id": "uuid",
  "statistics": {
    "open_issues": 10,
    "total_dependencies": 25,
    "average_priority": "HIGH"
  },
  "issues": [...]
}
```

**Root Cause Analysis:**
```python
# POST /api/v1/analyze/root-cause
{
  "test_name": "test_user_login",
  "error_message": "Authentication failed",
  "component": "auth-service",
  "labels": ["auth", "security"]
}
# Returns causal links with scores
```

## Business Value

Complete analysis capabilities are essential for the project's value proposition. Users need both impact and root cause analysis.

## Status: COMPLETED