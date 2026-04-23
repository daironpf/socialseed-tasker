# Issue #61: Add issue filter by project in API and CLI

## Description

Neither the API nor the CLI supports filtering issues by project name. All issues are returned regardless of which project they belong to, making it impossible to work with multiple projects in the same Neo4j instance.

## Problem Found

During the ecommerce test, the API returned 13 issues total - 8 for `shoe-ecommerce` plus 5 leftover issues from previous testing (`test-project`, `social-network`, `cli-test`). There is no `?project=` parameter on the issues endpoint.

Components already support `?project=` filtering, but issues do not.

## Impact

- Cannot isolate work to a single project
- Mixed results from all projects clutter the view
- CLI and frontend show unrelated issues from other projects

## Suggested Fix

- Add `project` query parameter to `GET /api/v1/issues`
- Filter by joining issue to component and matching `component.project`
- Add `--project` flag to `tasker issue list` CLI command
- Update frontend to accept project filter

## Priority

HIGH

## Labels

api, cli, feature, multi-project
