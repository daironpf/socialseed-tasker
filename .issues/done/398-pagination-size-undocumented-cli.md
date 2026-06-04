# Issue #398: Pagination size undocumented in CLI help

## Description

The default page_size of 20 for issue listing is not documented in --help or error messages. Users must discover pagination via `page` and `page_size` parameters through trial and error.

## Expected Behavior
`tasker issue list --help` should mention pagination options.

## Actual Behavior
No mention of page_size or pagination in help output.

## Steps to Reproduce
1. Run `tasker issue list --help`
2. No pagination-related options shown
3. With 50+ issues, only 20 appear

## Status: PENDING

## Priority: LOW

## Component
CLI / Documentation

## Suggested Fix
Add to `tasker issue list --help`: "Use --page and --page-size for pagination (default: 20 per page)".

## Impact
Users/agents don't know about pagination and may think data is missing.
