# Issue #01: Generate Hexagonal Feature-Oriented Directory Structure

## Description

Create the complete directory structure for the `socialseed-tasker` project following the **Hexagonal Architecture** organized by **Functional Features**. This structure is the foundation of the entire project and must be strictly adhered to by all subsequent development.

### Required Structure

```
src/
  socialseed_tasker/
    core/                          # The "Brain" - Pure Python, no external dependencies
      task_management/             # Entities (Task/Issue) and Actions (Create, Close, Move)
        __init__.py
        entities.py
        actions.py
        value_objects.py
      project_analysis/            # Rules for Graph dependencies and Architecture constraints
        __init__.py
        rules.py
        analyzer.py
    entrypoints/                   # How the world talks to us
      terminal_cli/                # Typer-based CLI implementation
        __init__.py
        commands.py
        app.py
      web_api/                     # FastAPI-based REST implementation
        __init__.py
        routes.py
        app.py
    storage/                       # How we remember things
      graph_database/              # Neo4j driver and Cypher queries
        __init__.py
        driver.py
        repositories.py
        queries.py
      local_files/                 # Markdown/JSON fallback for offline environments
        __init__.py
        file_store.py
        repositories.py
    bootstrap/                     # Dependency injection and system wiring
      __init__.py
      container.py
      wiring.py
tests/
  unit/
  integration/
  e2e/
docker-compose.yml
Dockerfile
pyproject.toml
README.md
LICENSE
```

### Architectural Constraints

- **`core/`** must be pure Python with NO external dependencies (no Neo4j, no FastAPI, no Typer)
- All external integrations must go through `storage/` or `entrypoints/`
- The Repository Pattern must be used so `core` logic can switch between `local_files` and `graph_database` without changes
- All code, comments, and documentation must be in **English**

### Business Value

This structure enforces separation of concerns, testability, and the ability to swap storage backends without touching business logic. It enables both CLI and API entrypoints to share the same core domain logic.

## Status: COMPLETED
