# Skill: Hexagonal Architecture Conventions

## Description

This project follows a **Feature-Oriented Hexagonal Architecture**. All code must adhere to these structural rules.

## Directory Structure

```
src/socialseed_tasker/
├── core/                      # Pure Python - NO external dependencies
│   ├── task_management/       # Entities, actions, value objects
│   ├── project_analysis/     # Rules, analyzers
│   ├── validation/          # Input validators
│   └── services/             # Webhook, Markdown, Secret managers
├── entrypoints/               # External interfaces
│   ├── terminal_cli/         # Typer + Rich CLI
│   └── web_api/             # FastAPI REST API
├── storage/                  # Persistence backends
│   └── graph_database/      # Neo4j implementation (ONLY storage backend)
├── bootstrap/               # Dependency injection & wiring
└── assets/                 # Templates for scaffolding
```

## Golden Rules

### `core/` - The Brain

- **NO** imports from Neo4j, FastAPI, Typer, Rich, or any external framework
- Only stdlib + Pydantic allowed
- Contains entities, actions (business logic), value objects
- Uses Repository Pattern via `Protocol` interfaces

### `entrypoints/` - How the World Talks to Us

- CLI code goes in `entrypoints/terminal_cli/`
- API code goes in `entrypoints/web_api/`
- **NO** business logic - delegate to `core/` actions
- Use dependency injection to get repositories

### `storage/` - How We Remember Things

- Neo4j code goes in `storage/graph_database/`
- **ONLY** Neo4j storage is supported (file storage removed)
- Must implement interfaces defined in `core/`
- **NO** business logic - only data access

### `bootstrap/` - Dependency Injection

- Wires everything together at startup
- Configuration via environment variables
- **ONLY** configures Neo4j storage backend

## Repository Pattern

All storage backends implement the same interface from `core/`:

```python
class TaskRepositoryInterface(Protocol):
    def create_issue(self, issue: Issue) -> None: ...
    def get_issue(self, issue_id: UUID) -> Issue | None: ...
    # ...
```

This interface allows for potential future storage backends while keeping `core/` logic storage-agnostic.

## Anti-Patterns to Avoid

- Importing `neo4j` in `core/` files
- Putting business logic in `entrypoints/` or `storage/`
- Importing `fastapi` or `typer` in `core/` files
- Creating circular dependencies between modules
- Using global state instead of dependency injection

## v0.8.0 New Modules

### validation/ (New in v0.8.0)

Input sanitization and validation:
- InputValidator: XSS and injection prevention
- ComponentValidator, IssueValidator, DependencyValidator
- Sanitizer for Neo4j Cypher queries

### services/ (New in v0.8.0)

Standalone services:
- WebhookSignatureValidator: GitHub webhook verification
- MarkdownTransformer: Graph to markdown conversion
- SecretManager: Secure credential handling