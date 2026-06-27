# Issue #238: Increase test coverage for API routes.py to 70%

## Description
The REST API routes module (routes.py) has only 44% test coverage with 1353 statements and 753 missing lines. Many endpoint combinations are untested.

## Expected Behavior
All API endpoints should have comprehensive test coverage.

## Actual Behavior
Only 44% coverage - missing tests for:
- Pagination edge cases
- Filtering combinations
- Error response formats
- Rate limiting behavior

## Steps to Reproduce
1. Run: `pytest tests/ --cov=socialseed_tasker/entrypoints/web_api/routes.py`
2. Observe: Low coverage report

## Status: COMPLETED

## Priority: MEDIUM

## Component
API

## Suggested Fix
Add tests for:
- `test_issues_pagination_page_out_of_range`
- `test_components_filter_by_project_invalid`
- `test_rate_limiting_returns_429`
- `test_analyze_impact_with_closed_issue`

## Impact
API edge cases may fail silently in production.

## Related Issues
- #124 (previous coverage effort)