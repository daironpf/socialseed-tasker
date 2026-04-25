# Issue #33: Add Labels Support to Issue Create/Update in CLI

## Description

The `issue create` and `issue update` commands should support labels but the current implementation doesn't properly pass them. The `--labels` option exists but needs testing and fixing.

### Requirements

- Test `tasker issue create --labels tag1,tag2` 
- Add `issue update` command with labels support
- Support labels in API as well
- Add tests

### Technical Details

File: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

Current issue_create:
```python
labels: str | None = typer.Option(None, "--labels", "-l", help="Comma-separated labels"),
```

Need to parse the comma-separated string into a list.

### Business Value

Labels are important for categorization and filtering. This is core functionality.

## STATUS: COMPLETED