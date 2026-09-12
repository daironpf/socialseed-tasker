# Issue #442: Fix closed_at silently dropped on issue close

## Description
When closing an issue, `closed_at` was sent but the `IssueUpdate` model didn't include it, so it was silently discarded. This broke resolution time metrics.

## Status: COMPLETED

## Priority: HIGH

## Changes Made
1. Added `closed_at: Optional[str] = None` to `IssueUpdate` model in `server.py`
2. PATCH handler now persists `closed_at` when provided

## Related Issues
- None
