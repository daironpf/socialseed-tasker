# Issue #20: Add CLI Commands for Component Update and Delete

## Description

The CLI currently supports `component create`, `component list`, and `component show`, but has no way to update or delete components. This creates an asymmetry with issues (which have full CRUD) and forces users to manually edit JSON files or use the API.

### Requirements

- Add `component update` command: change name, description, or project
- Add `component delete` command: remove a component (with confirmation, `--force` flag)
- Deleting a component should either reject if it has issues, or move its issues to an "Unassigned" component
- Add corresponding API endpoints if they don't exist (`PATCH /components/{id}`, `DELETE /components/{id}`)
- Write tests for both CLI commands

### Technical Details

File: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

New commands:
```python
@component_app.command("update")
def component_update(
    component_id: str,
    name: str | None = typer.Option(None, "--name", "-n"),
    description: str | None = typer.Option(None, "--description", "-d"),
    project: str | None = typer.Option(None, "--project", "-p"),
) -> None: ...

@component_app.command("delete")
def component_delete(
    component_id: str,
    force: bool = typer.Option(False, "--force", "-f"),
) -> None: ...
```

Need to add to `TaskRepositoryInterface`:
```python
def update_component(self, component_id: str, updates: dict) -> Component: ...
def delete_component(self, component_id: str) -> None: ...
```

Expected file paths:
- `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`
- `src/socialseed_tasker/core/task_management/actions.py` (new actions)
- `src/socialseed_tasker/storage/graph_database/repositories.py`
- `src/socialseed_tasker/storage/local_files/repositories.py`
- `src/socialseed_tasker/entrypoints/web_api/routes.py`
- `tests/unit/test_actions.py`

### Business Value

Completes the component CRUD lifecycle. Without this, users create components they can never modify or remove, leading to stale data.

## Status: COMPLETED
