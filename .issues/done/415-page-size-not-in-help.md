# Issue #415: `--page-size` option not shown in `--help`

## Description
The `issue list` command supports `--page` and `--page-size` options (visible when pagination is triggered), but they are not displayed in `tasker issue list --help`. Users can only discover them via trial-and-error or by reading source code.

## Expected Behavior
`tasker issue list --help` should show all available options including `--page` and `--page-size`.

## Actual Behavior
`--help` only shows basic options. Pagination options are missing from help output.

## Steps to Reproduce
1. `tasker issue list --help`
2. Observe no mention of `--page` or `--page-size`

## Status: RESOLVED

## Priority: LOW

## Component
CLI — issue list command

## Suggested Fix
Add `--page` and `--page-size` as documented Typer options with help text.

## Impact
Low — power users and CI scripts may need these flags.

## Related Issues
- (none)

## Changes Made
Already resolved by commit `d2abecd` (Fix #398: add --page and --page-size options to 'tasker issue list'). The `--page` and `--page-size` Typer options were properly defined in `src/socialseed_tasker/cli/commands/issue_commands.py:187-188` with help text, and are displayed in `tasker issue list --help`.

## Verification
`tasker issue list --help` shows both `--page` and `--page-size` in the options list.
