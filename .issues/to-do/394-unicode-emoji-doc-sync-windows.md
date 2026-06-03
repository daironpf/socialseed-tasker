# Issue #394: Unicode emoji causes charmap encoding error in doc-sync on Windows

## Description
The `tasker doc-sync` command uses emoji characters (e.g., `\U0001f4c4` for 📄) in its output, which causes a `charmap` codec encoding error on Windows PowerShell terminals that don't support Unicode characters.

## Expected Behavior
`tasker doc-sync` output should use ASCII-safe characters (e.g., `[FILE]`, `[LINK]`, `[*]`) on Windows terminals to avoid encoding errors.

## Actual Behavior
Running `tasker doc-sync` on Windows PowerShell produces: `Error: 'charmap' codec can't encode character '\U0001f4c4' in position 2: character maps to <undefined>`

## Steps to Reproduce
1. Run: `tasker doc-sync`
2. Observe: UnicodeEncodeError on Windows PowerShell terminal

## Status: PENDING

## Priority: LOW

## Component
CLI (`doc_sync_commands.py`)

## Suggested Fix
Replace emoji characters with ASCII-safe alternatives in `doc_sync_commands.py`. Use `[FILE]` instead of `📄`, `[LINK]` instead of `🔗`. Alternatively, check `sys.stdout.encoding` and conditionally use emoji only when encoding supports it.

## Impact
Minor. Functionality is unaffected. Only the display output breaks on Windows terminals without Unicode support.

## Related Issues
- #392 (doc-sync command)

## Changes Made
[Leave empty]

## Verification
[Leave empty]
