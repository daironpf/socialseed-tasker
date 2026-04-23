# Issue #21: Enable Neo4j Backend Support in CLI

## Description

The CLI (`terminal_cli/commands.py`) hardcodes `FileTaskRepository` and the `.tasker-data` directory. There is no way to use the Neo4j backend from the command line, despite the architecture fully supporting it through the `Container` and `AppConfig`.

### Requirements

- Replace the hardcoded `get_repository()` function with repository selection from `Container`
- Add a `--backend` global option (`file` or `neo4j`) to the CLI app
- Read Neo4j connection settings from environment variables (already supported by `AppConfig.from_env()`)
- Add a `tasker status` command showing current backend, connection status, and data directory
- Ensure all existing CLI commands work with both backends

### Technical Details

File: `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`

Current:
```python
def get_repository() -> TaskRepositoryInterface:
    _data_dir.mkdir(parents=True, exist_ok=True)
    return FileTaskRepository(_data_dir)
```

Should use:
```python
from socialseed_tasker.bootstrap.container import Container

def get_repository() -> TaskRepositoryInterface:
    container = Container.from_env()
    return container.get_repository()
```

Add global option to `app.py`:
```python
@app.callback()
def main(
    backend: str = typer.Option("file", "--backend", envvar="TASKER_STORAGE_BACKEND"),
) -> None: ...
```

Expected file paths:
- `src/socialseed_tasker/entrypoints/terminal_cli/app.py`
- `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`
- `src/socialseed_tasker/bootstrap/container.py`

### Business Value

Unifies the CLI and API to use the same configuration. Users running Neo4j for the API can use the same database from the CLI. Removes the `sys.path` hack in commands.py since the Container handles imports properly.

## Status: COMPLETED
