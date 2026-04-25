# Issue #67: Add data cleanup/reset endpoint for testing

## Description

There is no way to clear all data from the system without manually deleting issues one by one or dropping the Neo4j database. This makes testing and demos cumbersome.

## Problem Found

After the ecommerce setup test, the database contained 13 issues (8 new + 5 from previous tests). Cleaning up required either:
- Individual DELETE requests for each issue
- Dropping the Neo4j volume and restarting Docker Compose

## Impact

- Testing workflows requires manual cleanup between runs
- Demo environments accumulate stale data
- No way to start fresh without full Docker restart

## Suggested Fix

- Add `POST /api/v1/admin/reset` endpoint (DEBUG mode only or with admin auth)
- Add `tasker reset --force` CLI command with confirmation prompt
- Support partial reset: `--issues-only`, `--components-only`, `--all`
- Document in testing section of README

## Dependencies

- Depends on #58 (Fix stale Docker image) - should be part of the same release cycle

## Priority

LOW

## Labels

cli, api, testing, dx
