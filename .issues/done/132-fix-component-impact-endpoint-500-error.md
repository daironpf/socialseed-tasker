# Fix Component Impact endpoint returning 500 error

**Status**: OPEN
**Priority**: HIGH
**Labels**: bug, api
**Created**: 2026-04-12

## Problem

The API endpoint `/api/v1/analyze/component-impact/{id}` returns a 500 Internal Server Error with message:

```
NameError: name 'ComponentImpactIssueSummary' is not defined
```

## Location

`src/socialseed_tasker/entrypoints/web_api/routes.py:1355`

## Error Traceback

```
File "routes.py", line 1354, in analyze_component_impact
  affected_issues_summary=[
File "routes.py", line 1355, in <listcomp>
  ComponentImpactIssueSummary(id=i.id, title=i.title, status=i.status) for i in impact.affected_issues_summary
NameError: name 'ComponentImpactIssueSummary' is not defined
```

## Expected Behavior

The endpoint should return component impact analysis with affected issues summary.

## Test Command

```bash
curl -s "http://localhost:8000/api/v1/analyze/component-impact/1fa8d747-46bc-4034-9400-442c93a0832b"
```

## Suggestions

1. Import `ComponentImpactIssueSummary` from the core module
2. Verify it's properly defined in `core.project_analysis.analyzer`
3. Add unit test for component impact endpoint