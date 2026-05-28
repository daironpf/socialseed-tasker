# Issue #342: Emoji in error message causes UnicodeEncodeError on Windows

## Description
When attempting to close an issue with open dependencies, the CLI tries to display an emoji character (`\U0001f4a1` / 💡) in the error message. On Windows with `charmap` encoding (e.g., Spanish locale), this raises a `UnicodeEncodeError` instead of showing the intended error message. The full traceback is dumped to the terminal.

## Expected Behavior
Error message should be displayed cleanly without traceback, regardless of locale/encoding.

## Actual Behavior
```
Error: 'charmap' codec can't encode character '\U0001f4a1' in position 0: character maps to <undefined>
```
Followed by a full Python traceback.

## Steps to Reproduce
1. Create issue A
2. Create issue B that depends on A (do not close A)
3. Run `tasker issue close <B-id>` on Windows with Spanish locale

## Status: COMPLETED

## Priority: HIGH

## Component
CLI

## Suggested Fix
Replace emoji characters with ASCII-safe alternatives or use `errors='replace'` when encoding output. Ensure error messages are encoding-agnostic on all platforms.

## Impact
Users see a raw Python traceback instead of a readable error. Exit code is correctly 1, but UX is poor.

## Related Issues
- FIND-001 from black-box evaluation 2026-05-28
