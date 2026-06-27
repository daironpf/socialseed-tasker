# Issue #284: Bulk issue creation script fails on Windows

## Description
The issue creation script (Python subprocess with curl) only created 10 issues instead of 50. PowerShell and Python encoding issues prevented bulk creation.

## Expected Behavior
Script should create 50 issues when requested.

## Actual Behavior
- Python subprocess + curl commands only created 10 issues
- PowerShell Invoke-RestMethod had JSON parsing issues with escaped quotes

## Steps to Reproduce
1. Run create_50.py script
2. Expected: 50 issues
3. Actual: 10 issues (from previous test run)

## Status: COMPLETED

## Priority: LOW

## Component
API

## Suggested Fix
- Use direct urllib in Python instead of subprocess curl
- Or fix PowerShell JSON string escaping

## Impact
Bulk issue creation is problematic on Windows.

## Related Issues
- Related to Real-Test evaluation workflow (2026-05-13)
- FIND-003 from report.md