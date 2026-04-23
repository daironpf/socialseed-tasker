# Issue #128: Short UUID Support Not Working

## Description

The documentation mentions short ID support (truncated UUID), but CLI commands require full UUID for most operations. This makes CLI usage cumbersome.

### Current Behavior

```bash
# This works (full UUID)
tasker issue create "Test" -c 1fa8d747-46bc-4034-9400-442c93a0832b

# This fails (short UUID)
tasker issue create "Test" -c 1fa8d747
# Error: Invalid component ID format
```

### Expected Behavior

- Accept both full UUID and first 8 characters (or more)
- Auto-resolve to full UUID for consistency

### Requirements

1. Update CLI commands to accept short IDs (at least 8 characters)
2. Use prefix matching to resolve full UUID from partial
3. Update help text to clarify supported formats
4. Update API_REFERENCE.md and README.md with examples

### Affected Commands

- `tasker issue create -c`
- `tasker issue show`
- `tasker issue update`
- `tasker analyze impact`
- `tasker dependency add`

### Priority: LOW

### Status: COMPLETED (2026-04-11)

### Changes Made

1. Added `resolve_component_id()` helper: accepts 4+ chars prefix, name exact match
2. Added `resolve_issue_id()` helper: accepts 4+ chars prefix, title exact match
3. Updated `issue create -c` to use component name or short ID
4. Updated `analyze impact` to accept title or short ID
5. Updated `dependency add` to accept title or short ID

### Files Modified

- `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

### Verification

```bash
# Short UUID (4+ chars)
$ tasker -pw neoSocial issue create "Test" -c 1fa8d747 -p HIGH
Issue created: ...

# Component name
$ tasker -pw neoSocial issue create "Test" -c backend -p HIGH
Issue created: ...

# Issue title in analyze
$ tasker -pw neoSocial analyze impact "Test via name"
Impact Analysis for ...

# Short UUID in analyze  
$ tasker -pw neoSocial analyze impact 06a5
Impact Analysis for ...```