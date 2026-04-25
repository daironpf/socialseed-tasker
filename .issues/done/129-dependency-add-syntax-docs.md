# Issue #129: Dependency Add Syntax Inconsistency in Documentation

## Description

Documentation shows `--depends-on` flag for dependency add, but actual CLI syntax uses positional arguments.

### Current Behavior (Actual)

```bash
tasker dependency add ISSUE_ID DEPENDS_ON
```

### Documentation Example (Incorrect)

```bash
tasker dependency add ISSUE_ID --depends-on DEPENDS_ON
```

### Requirements

1. Update README.md examples to show correct syntax
2. Update API_REFERENCE.md with correct CLI syntax
3. Update CLI help text if needed for clarity
4. Check all other commands for similar inconsistencies

### Files to Check

- `README.md`
- `API_REFERENCE.md`
- `.agent/skills/environment-tooling.md`

### Priority: LOW

### Status: COMPLETED (2026-04-11)

### Changes Made

1. Fixed API_REFERENCE.md: Changed `<issue> --depends-on <dep>` to `<issue_id> <depends_on>`
2. CLI help shows correct positional syntax (no changes needed)

### Files Modified

- `API_REFERENCE.md`

### Verification

```bash
# CLI help shows correct syntax
$ tasker dependency add --help
Usage: tasker dependency add [OPTIONS] ISSUE_ID DEPENDS_ON

# Documentation matches
$ cat API_REFERENCE.md | grep dependency
tasker dependency add <issue_id> <depends_on>
```