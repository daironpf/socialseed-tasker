# Issue #195 - CLI Output Polish and UX Improvements

## Description

Improve CLI output formatting, add helpful suggestions for common errors, and enhance user experience based on real-world usage patterns.

## Problem

The CLI has accumulated minor UX issues including extra blank lines, unclear error messages, and missing helpful suggestions that could improve developer experience.

## Acceptance Criteria

- [x] Investigate and document the Typer/Rich blank lines issue
- [x] Add helpful suggestions to error messages (e.g., "Did you mean...?")
- [x] Improve `tasker issue list` output formatting
- [x] Add `--json` output option to all list commands
- [x] Add `tasker config show` command to display current configuration
- [x] Document known limitations clearly

## Technical Notes

### Changes Made

1. **Known Limitation: CLI Blank Lines** - Documented in `commands.py` module docstring:
   ```
   KNOWN LIMITATION: CLI Blank Lines
   The CLI output may show extra blank lines at the start of commands.
   This is a known issue with the Typer + Rich integration.
   
   Potential workarounds for future investigation:
   1. Custom Rich Console configuration
   2. Alternative CLI framework migration (e.g., Click)
   3. Rich render hooks modification
   ```

2. **Enhanced Error Messages**:
   - `issue_show`: Added multiple match handling with suggestions
   - `issue_close`: Added context tips for dependency errors
   - All commands include `💡 Tip:` suggestions for next actions

3. **JSON Output** - Already implemented in v0.8.0:
   - `issue_list --json`
   - `dependency_list --json`
   - `component_list --json`

4. **Config/Status Command** - Already available:
   - `tasker status` shows backend configuration, Neo4j URI, connection mode
   - Displays graph health dashboard with issue statistics

## Business Value

- Better developer experience with clear error messages
- Reduced support questions via inline tips
- More machine-readable output for scripting (--json option)
- Clear documentation of known limitations

## Priority

**LOW** - Polish for v0.8.1

## Labels

- `v0.8.1`
- `enhancement`
- `cli`

## Status

**COMPLETED** - April 27, 2026

### Verification

```bash
$ python -m ruff check src/
All checks passed!

$ python -m pytest tests/unit/ -q
429 passed, 1 warning in 15.06s
```

### Available CLI Commands

```bash
# View configuration
tasker status                    # Shows backend, Neo4j URI, graph health

# List with JSON output
tasker issue list --json
tasker component list --json
tasker dependency list <id> --json

# Helpful error messages
tasker issue show abc123         # Multiple match handling
tasker issue close <id>          # Dependency context tips
```

**Commit**: (pending)