# Issue #35: Add Root Cause Analysis CLI Command

## Description

The API has root cause analysis (`POST /analyze/root-cause`) and impact analysis (`GET /analyze/impact/{id}`) but the CLI doesn't expose these useful features. Users should be able to analyze issues from the command line.

### Requirements

- Add `tasker analyze root-cause` command that takes test failure info
- Add `tasker analyze impact <issue_id>` command
- Output results in human-readable format (Rich tables/panels)
- Add tests

### Technical Details

File: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

New commands:
```python
@analyze_app.command("root-cause")
def analyze_root_cause(
    test_name: str,
    error_message: str,
    component: str,
    ...
): ...

@analyze_app.command("impact")
def analyze_impact(
    issue_id: str,
): ...
```

### Business Value

Makes powerful analysis features accessible from CLI, useful for debugging workflows.

## STATUS: COMPLETED