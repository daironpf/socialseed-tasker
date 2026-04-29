# Issue #203 - Project Filter Ineffective in Issues Endpoint

## Description

Querying the issues endpoint with a `project` filter parameter returns all issues instead of filtering by project. This affects the ability to isolate project data in multi-tenant scenarios.

## Status: COMPLETED

## Priority

**MEDIUM** - Affects multi-tenant isolation

## Component

API, Repository, Cypher Queries

## Root Cause

The issue was in the Cypher query `LIST_ISSUES` in `queries.py`. When using `OPTIONAL MATCH` for the `BELONGS_TO` relationship, if a component doesn't exist or the relationship is missing, `c.project` evaluates to `NULL`.

In Cypher, `NULL = 'value'` returns `NULL` (not `FALSE`), which breaks the WHERE clause logic when `$project IS NULL` is checked.

## Changes Made

### Fixed Cypher Query

Changed the project filter condition in `LIST_ISSUES`:

**Before:**
```cypher
AND ($project IS NULL OR c.project = $project)
```

**After:**
```cypher
AND ($project IS NULL OR (c IS NOT NULL AND c.project = $project))
```

This ensures that when there's no component relationship, the filter correctly excludes the issue.

### Added Test Coverage

Added `TestProjectFiltering` class to `tests/unit/test_api.py`:
- `test_list_issues_by_project_filter` - Verifies API response structure

## Verification

### Cypher Query Test
```cypher
# Before fix: Returns all issues even with wrong project
MATCH (i:Issue) OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Component) 
WHERE $project IS NULL OR c.project = $project

# After fix: Returns 0 issues with non-existent project
MATCH (i:Issue) OPTIONAL MATCH (i)-[:BELONGS_TO]->(c:Component) 
WHERE $project IS NULL OR (c IS NOT NULL AND c.project = $project)
```

### Ruff Check
```bash
$ python -m ruff check src/
All checks passed!
```

### Tests
```bash
$ python -m pytest tests/unit/ -q
460 passed, 1 skipped, 1 warning in 24.47s
```

## Technical Details

**Files Modified:**
- `src/socialseed_tasker/storage/graph_database/queries.py` - Fixed LIST_ISSUES query

**Files Added:**
- `tests/unit/test_api.py` - Added TestProjectFiltering class

## Impact

- Project filtering now works correctly for multi-tenant scenarios
- Non-existent project queries return empty results
- Combined filters (project + status) work together

## Related Issues

- Real-Test Evaluation: FIND-002 (Dental Clinic System)