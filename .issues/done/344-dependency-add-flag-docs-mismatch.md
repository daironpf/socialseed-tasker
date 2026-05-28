# Issue #344: CLI uses positional args for dependency, not --depends-on flag

## Description
The AGENT_GUIDE.md documents `tasker dependency add <issue-2-id> --depends-on <issue-1-id>` but the actual CLI expects positional arguments: `tasker dependency add <issue_id> <depends_on>`. Running with `--depends-on` yields "No such option: --depends-on".

## Expected Behavior
Either the AGENT_GUIDE.md should be updated to reflect the correct syntax, OR the CLI should support both `--depends-on` flag and positional arguments.

## Actual Behavior
- `tasker dependency add --help` shows: `Usage: tasker dependency add [OPTIONS] ISSUE_ID DEPENDS_ON`
- AGENT_GUIDE.md shows: `tasker dependency add <issue> --depends-on <dep>`

## Steps to Reproduce
1. Run `tasker dependency add <id> --depends-on <id2>`
2. Observe: "No such option: --depends-on"

## Status: COMPLETED

## Priority: LOW

## Component
CLI

## Suggested Fix
Update AGENT_GUIDE.md to match actual CLI syntax, or add `--depends-on` as an alias option.

## Impact
Low - the CLI help text is correct, but AI agents following AGENT_GUIDE.md will fail.

## Related Issues
- FIND-003 from black-box evaluation 2026-05-28
