# Issue #281: Issue creation returns different ID formats

## Description
Some issue creation responses return simple IDs like "issue-1" while others return full UUIDs. This inconsistency makes it harder to track issues programmatically.

## Expected Behavior
All issue creation responses should return consistent UUID format.

## Actual Behavior
- First batch of created issues returned "issue-1", "issue-2", etc.
- Later batch returned full UUIDs like "8465307d-5952-403f-bcc6-bc859bfe2b06"

## Steps to Reproduce
1. Create multiple issues via API
2. Compare the ID format in responses

## Status: PENDING

## Priority: LOW

## Component
API

## Suggested Fix
Standardize the issue ID generation to always return UUID format in the API response, regardless of how the issue was created (batch vs individual).

## Impact
Makes it more complex to write scripts that depend on issue IDs. External tools expecting UUID format may fail.

## Related Issues
- Related to Real-Test evaluation workflow (2026-05-12)