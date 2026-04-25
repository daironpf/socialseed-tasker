# Issue #59: Add component names to CLI issue list output

## Description

The CLI `tasker issue list` command shows component UUIDs instead of human-readable component names, making it hard to identify which component each issue belongs to.

## Problem Found

Running `tasker issue list` showed:
```
| ID       || Status     | Priority   | Component                             |
| 9076ae1c || OPEN       | MEDIUM     | d904a300                              |
| 37210caf || OPEN       | CRITICAL   | d2aff9f3                              |
```

The Component column shows truncated UUIDs like `d904a300` instead of `admin-dashboard` or `checkout-payment`.

## Impact

- Users must cross-reference component IDs manually
- Reduces usability of CLI for day-to-day work
- Makes it hard to quickly scan issues by component

## Suggested Fix

- In `commands.py`, modify `list_issues` to fetch component names alongside issues
- Join issues with their component data and display `component.name` instead of `component_id`
- If component lookup fails, fall back to showing short UUID

## Priority

MEDIUM

## Labels

cli, ux, enhancement
