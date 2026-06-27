# Issue #283: CLI Unicode encoding error on Windows

## Description
CLI commands fail with UnicodeEncodeError when Rich tries to print emoji characters on Windows.

## Expected Behavior
CLI should display correctly on Windows without encoding errors.

## Actual Behavior
```
UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f4a1' in position 0
```

## Steps to Reproduce
1. Run `tasker component list` on Windows
2. Error occurs when Rich tries to print emoji tip

## Status: COMPLETED

## Priority: MEDIUM

## Component
CLI

## Suggested Fix
- Set PYTHONIOENCODING=utf-8 environment variable
- Configure Rich console to handle Windows encoding
- Remove emoji from CLI output or use text alternatives

## Impact
CLI unusable on Windows for commands that output Rich-formatted text.

## Related Issues
- Related to Real-Test evaluation workflow (2026-05-13)
- FIND-002 from report.md