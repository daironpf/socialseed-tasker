# Developer Onboarding Guide - Tasker v1.0.0

Welcome to Tasker! This guide will help you get up and running in minutes and understand how to contribute to the project.

## Quick Start (5 minutes)

```bash
# 1. Clone the repository
git clone https://github.com/your-org/tasker.git
cd tasker

# 2. Install dependencies
pip install -e .

# 3. Start Neo4j via Docker
docker compose up -d tasker-db

# 4. Initialize Tasker in your project
tasker init .

# 5. Start the API
tasker api
```

The API will be available at `http://localhost:8000` and the Neo4j browser at `http://localhost:7474`.

## Prerequisites

- **Python**: 3.10+ (3.11 recommended)
- **Neo4j**: 5.x (via Docker)
- **Docker & Docker Compose**
- **Git**
- **Node.js**: 18+ (for frontend development)

## Architecture Overview

Tasker implements a three-pillar architecture:

### 1. Organizational Pillar
```
Project → Component → Issue
```
- **Project**: Root container for components and issues
- **Component**: Groups related issues (e.g., "Frontend", "API", "Database")
- **Issue**: Task unit with status, priority, and assignments

### 2. Code-as-Graph Pillar
```
CodeFile → CodeSymbol → CodeImport
```
- Tracks source code structure in Neo4j
- Enables impact analysis and dependency mapping
- Supports semantic search via RAG embeddings

### 3. Intelligence Pillar
```
Agent → ReasoningNode → Commit
```
- Agent swarm coordination
- Decision logging and reasoning tracking
- Commit-to-issue linkage for traceability

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Project    │────▶│ Component   │────▶│   Issue    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                                       │
       ▼                                       ▼
┌─────────────┐                         ┌─────────────┐
│    Agent    │────▶ ReasoningNode ───▶│   Commit    │
└─────────────┘                         └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  CodeFile   │────▶│ CodeSymbol  │────▶│CodeImport   │
└─────────────┘     └─────────────┘     └─────────────┘
```

## Directory Walkthrough

### `src/socialseed_tasker/core/`
**What it contains**: Business logic entities, validation, and domain rules.

| Subdirectory | Purpose | Example File |
|--------------|---------|--------------|
| `task_management/` | Core entities (Issue, Component, Project) | `entities.py` |
| `project_analysis/` | Impact analysis, rules, constraints | `analyzer.py`, `rules.py` |
| `validation/` | Input validation and sanitization | `validators.py`, `input_sanitizer.py` |
| `system_init/` | Project scaffolding and initialization | `scaffolder.py` |

**What DOESN'T belong here**: Storage implementation, API routes, CLI commands.

### `src/socialseed_tasker/storage/`
**What it contains**: Data persistence and external integrations.

| Subdirectory | Purpose | Example File |
|--------------|---------|--------------|
| `graph_database/` | Neo4j repositories and queries | `repositories.py`, `queries.py` |
| `adapters/` | External service adapters | `github/__init__.py` |

**What DOESN'T belong here**: Business logic, validation rules.

### `src/socialseed_tasker/entrypoints/`
**What it contains**: External interfaces (API, CLI, Web).

| Subdirectory | Purpose | Example File |
|--------------|---------|--------------|
| `web_api/` | FastAPI routes and schemas | `routes.py`, `app.py` |
| `terminal_cli/` | Typer CLI commands | `commands.py` |
| `cli/` | CLI entry points | `init_command.py` |

### `src/socialseed_tasker/bootstrap/`
**What it contains**: Dependency injection and wiring.

| Subdirectory | Purpose | Example File |
|--------------|---------|--------------|
| `wiring.py` | Driver and repository initialization | |
| `container.py` | Dependency container | |

### `src/socialseed_tasker/assets/`
**What it contains**: Templates and static assets.

| Subdirectory | Purpose |
|--------------|---------|
| `templates/` | Project templates for `tasker init` |
| `frontend/` | Built frontend assets |

## Your First Feature

Follow this step-by-step guide to implement a small feature:

### Step 1: Create an Issue
Create an issue file in `.issues/to-do/` or use the CLI:
```bash
tasker issue create --title "Add new feature" --component "my-component"
```

### Step 2: Implement in Core
Add your business logic in `core/`. Define entities in `core/task_management/entities.py`:
```python
class MyEntity(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
```

### Step 3: Add to Repository
Add data access methods in `storage/graph_database/repositories.py`:
```python
def get_my_entity(self, entity_id: UUID) -> MyEntity | None:
    with self._driver.session() as session:
        result = session.run("MATCH (e:MyEntity {id: $id}) RETURN e", id=str(entity_id))
        record = result.single()
        if record:
            return MyEntity(**dict(record["e"]))
    return None
```

### Step 4: Add CLI Command
Add a command in `entrypoints/terminal_cli/commands.py`:
```python
@my_app.command("get-entity")
def get_entity(entity_id: str) -> None:
    repo = get_repository()
    entity = repo.get_my_entity(UUID(entity_id))
    console.print(f"[success]Entity:[/success] {entity.name}")
```

### Step 5: Add API Endpoint
Add an endpoint in `entrypoints/web_api/routes.py`:
```python
@my_router.get("/entities/{entity_id}")
def get_entity(entity_id: str) -> APIResponse[MyEntityResponse]:
    repo = get_repository()
    entity = repo.get_my_entity(UUID(entity_id))
    return APIResponse(data=entity_to_response(entity))
```

### Step 6: Write Tests
Create tests in `tests/unit/`:
```python
def test_get_entity():
    repo = get_repository()
    entity = repo.get_my_entity(test_uuid)
    assert entity is not None
```

### Step 7: Run Tests
```bash
pytest tests/unit/ -v
# Or with coverage
pytest tests/ --cov=src/socialseed_tasker --cov-report=html
```

### Step 8: Update Documentation
- Add to `docs/CLI_COMMANDS.md` if it's a new CLI command
- Add to `docs/API_REFERENCE.md` if it's a new API endpoint
- Update `VERSIONS.md` with your change

## Common Patterns

### Repository Pattern
All data access goes through repositories in `storage/graph_database/`. Each repository wraps Neo4j operations:

```python
class MyRepository:
    def __init__(self, driver: Neo4jDriver):
        self._driver = driver
    
    def _get_session(self):
        return self._driver.session(database="neo4j")
    
    def create(self, entity: MyEntity) -> None:
        with self._get_session() as session:
            session.run(queries.CREATE_MY_ENTITY, **entity.model_dump())
```

### Entity Definition in Core
Entities are defined in `core/task_management/entities.py` using Pydantic:

```python
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime

class MyEntity(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    description: str = ""
    created_at: datetime = Field(default_factory=datetime.now)
```

### API Endpoint Creation
Endpoints follow this pattern in `routes.py`:

```python
@my_router.get("/path", response_model=APIResponse[MyResponse])
def my_endpoint(
    param: str = Query(..., description="Description"),
    repo: MyRepository = Depends(get_repo),
) -> APIResponse[MyResponse]:
    result = repo.get_something(param)
    return APIResponse(data=result, meta=Meta(request_id=None))
```

### CLI Command Creation
Commands use Typer in `commands.py`:

```python
@my_app.command("my-command")
def my_command(
    param: str = typer.Option(..., "--param", "-p", help="Help text"),
) -> None:
    """Command description."""
    console.print(f"[info]Param:[/info] {param}")
```

## Testing

### How to Run Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_entities.py -v

# Run with coverage
pytest --cov=src/socialseed_tasker --cov-report=term-missing

# Run tests matching a pattern
pytest -k "test_entity"
```

### Test Structure

```
tests/
├── unit/              # Unit tests
│   ├── test_entities.py
│   ├── test_repositories.py
│   └── test_cli_commands.py
├── integration/       # Integration tests
│   └── test_neo4j_repository.py
├── conftest.py        # Shared fixtures
└── fakes/            # Fake implementations
    └── fake_neo4j_driver.py
```

### Writing New Tests

Use the existing patterns:
```python
def test_my_function():
    # Arrange
    my_input = "test"
    
    # Act
    result = my_function(my_input)
    
    # Assert
    assert result == expected
```

For repository tests, use the fake driver:
```python
from tests.fakes.fake_neo4j_driver import FakeNeo4jDriver

def test_repository():
    fake_driver = FakeNeo4jDriver()
    repo = MyRepository(fake_driver)
    result = repo.get_all()
    assert len(result) > 0
```

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Neo4j connection refused | Run `docker compose up -d tasker-db` |
| Import errors | Run `pip install -e .` to install package |
| Port already in use | Check if API is already running on port 8000 |
| Tests failing | Ensure Neo4j is running and schema is initialized |

### Debug Tips

1. **Enable debug logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check Neo4j browser**: Visit `http://localhost:7474` to browse the graph

3. **API health check**:
   ```bash
   curl http://localhost:8000/health
   ```

4. **CLI help**:
   ```bash
   tasker --help
   tasker issue --help
   ```

## Next Steps

### Good First Issues
Look for issues tagged with `good first issue` in the issues directory:
```bash
ls .issues/to-do/
```

### Architecture Deep Dives
- **Graph Data Model**: See `docs/GRAPH_MODEL.md`
- **Hexagonal Architecture**: See `.agent/project.md`
- **CLI Reference**: See `docs/CLI_COMMANDS.md`
- **API Reference**: See `docs/API_REFERENCE.md`
- **Code Graph**: See `docs/CODE_GRAPH_GUIDE.md`
- **RAG Guide**: See `docs/RAG_GUIDE.md`

### Useful Commands

| Command | Description |
|---------|-------------|
| `tasker init .` | Initialize Tasker in a project |
| `tasker issue list` | List all issues |
| `tasker issue create` | Create a new issue |
| `tasker code-graph scan .` | Scan code into graph |
| `tasker rag search "query"` | Search knowledge base |
| `tasker agent register` | Register an AI agent |
| `tasker api` | Start the API server |

---

For questions, check the FAQ in `docs/TROUBLESHOOTING.md` or ask in the community!