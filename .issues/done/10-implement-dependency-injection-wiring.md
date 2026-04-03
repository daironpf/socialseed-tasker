# Issue #10: Implement Dependency Injection and System Wiring

## Description

Build the bootstrap layer in `src/socialseed_tasker/bootstrap/`. This layer is responsible for dependency injection, configuration management, and wiring all components together at application startup.

### Requirements

#### Module Structure

**`container.py`** - Dependency injection container
- Service registry and resolver
- Singleton vs transient lifecycle management
- Configuration-based service selection (neo4j vs file storage)

**`wiring.py`** - Application assembly
- Wire together core, storage, and entrypoints
- Environment-based configuration loading
- Application lifecycle hooks (startup, shutdown)

#### Dependency Injection Container

The container must manage the following services:

```python
class Container:
    # Configuration
    def get_config() -> AppConfig: ...
    
    # Storage (selected based on configuration)
    def get_task_repository() -> TaskRepositoryInterface: ...
    def get_component_repository() -> ComponentRepositoryInterface: ...
    
    # Neo4j (if selected)
    def get_neo4j_driver() -> AsyncGraphDatabase.driver: ...
    
    # Core Actions
    def get_issue_actions() -> IssueActions: ...
    def get_dependency_actions() -> DependencyActions: ...
    def get_component_actions() -> ComponentActions: ...
```

#### Configuration Management

**`AppConfig` Pydantic Model:**
```python
class Neo4jConfig(BaseModel):
    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: str = ""
    database: str = "neo4j"
    max_connection_lifetime: int = 3600

class StorageConfig(BaseModel):
    backend: Literal["neo4j", "file"] = "neo4j"
    neo4j: Neo4jConfig = Neo4jConfig()
    file_path: Path = Path(".tasker-data")

class AppConfig(BaseModel):
    storage: StorageConfig = StorageConfig()
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
```

**Environment Variable Mapping:**
- `TASKER_STORAGE_BACKEND` -> `storage.backend`
- `TASKER_NEO4J_URI` -> `storage.neo4j.uri`
- `TASKER_NEO4J_USER` -> `storage.neo4j.user`
- `TASKER_NEO4J_PASSWORD` -> `storage.neo4j.password`
- `TASKER_FILE_PATH` -> `storage.file_path`
- `TASKER_API_HOST` -> `api_host`
- `TASKER_API_PORT` -> `api_port`
- `TASKER_DEBUG` -> `debug`

#### Wiring for CLI

```python
def wire_cli() -> CLIApp:
    container = Container.from_env()
    actions = container.get_actions()
    return CLIApp(actions=actions)
```

#### Wiring for API

```python
def wire_api() -> FastAPI:
    container = Container.from_env()
    app = FastAPI()
    
    @app.on_event("startup")
    async def startup():
        await container.initialize()
    
    @app.on_event("shutdown")
    async def shutdown():
        await container.cleanup()
    
    # Register routes with injected dependencies
    app.include_router(create_issue_router(container.get_task_repository))
    # ... other routers
    
    return app
```

#### Lifecycle Management
- **Startup**: Initialize Neo4j driver, verify connection, create indexes/constraints
- **Shutdown**: Close Neo4j driver gracefully, flush file caches
- **Health Check**: Verify storage backend is accessible

#### Neo4j Schema Initialization
On first startup with Neo4j backend, create necessary indexes and constraints:
```cypher
CREATE CONSTRAINT issue_id IF NOT EXISTS FOR (i:Issue) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT component_id IF NOT EXISTS FOR (c:Component) REQUIRE c.id IS UNIQUE;
CREATE INDEX issue_status IF NOT EXISTS FOR (i:Issue) ON (i.status);
CREATE INDEX issue_component IF NOT EXISTS FOR (i:Issue) ON (i.component_id);
CREATE INDEX issue_priority IF NOT EXISTS FOR (i:Issue) ON (i.priority);
```

### Requirements
- All bootstrap code stays in `bootstrap/`
- Container must be testable (allow mock service substitution)
- Configuration must have sensible defaults
- Environment variables must override defaults
- No circular dependencies between modules
- Clear error messages when configuration is invalid or services cannot be initialized

### Business Value

The bootstrap layer is the glue that holds the entire application together. Proper dependency injection enables testability (mock repositories in tests), configurability (switch storage backends via env vars), and maintainability (clear service boundaries). It ensures all components are properly wired together regardless of how the application is started (CLI or API).

## Status: COMPLETED
