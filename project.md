# SocialSeed Tasker - Project Overview

## Project Summary

**SocialSeed Tasker** is a graph-based task management framework for AI agents with Neo4j storage backend, hexagonal architecture, and comprehensive tooling for CLI and API interfaces.

---

## 1. Core Architecture (Hexagonal)

### Package Structure
```
src/socialseed_tasker/
├── core/                      # Domain logic (framework-agnostic)
│   ├── task_management/        # Entities, actions, value objects
│   ├── project_analysis/       # Rules, analyzers, policy engine
│   ├── validation/             # Input validation and sanitization
│   └── services/              # External integrations (webhooks, Markdown, secrets)
├── entrypoints/               # External interfaces
│   ├── terminal_cli/          # Typer-based CLI
│   └── web_api/              # FastAPI REST API
├── storage/                   # Neo4j persistence layer
├── bootstrap/                # Dependency injection & configuration
└── assets/                   # Templates for scaffolding
```

### Key Architectural Principles
- **Hexagonal Architecture**: Strict separation between core domain, entrypoints, and storage
- **Domain-Driven Design**: Entities, value objects, and services in `core/`
- **Repository Pattern**: Storage-agnostic interfaces in `core/`, implementations in `storage/`
- **No Framework Code in Core**: `core/` contains zero imports of FastAPI, Typer, or Neo4j drivers

---

## 2. Domain Model (Core Entities)

### Issue Entity (`core/task_management/entities.py`)
```python
class Issue(BaseModel):
    id: UUID
    title: str (max 200)
    description: str
    status: IssueStatus (OPEN, IN_PROGRESS, CLOSED, BLOCKED)
    priority: IssuePriority (LOW, MEDIUM, HIGH, CRITICAL)
    component_id: UUID
    labels: list[str]
    dependencies: list[UUID]      # Issues this depends on
    blocks: list[UUID]            # Issues that depend on this
    affects: list[UUID]           # Impact propagation
    architectural_constraints: list[str]
    agent_working: bool
    reasoning_logs: list[ReasoningLogEntry]
```

### Component Entity
```python
class Component(BaseModel):
    id: UUID
    name: str (unique per project)
    description: str | None
    project: str
```

### Constraint System (`core/task_management/constraints.py`)
- **Constraint Categories**: ARCHITECTURE, TECHNOLOGY, NAMING, PATTERNS, DEPENDENCIES
- **Constraint Levels**: HARD (blocks actions), SOFT (warnings)
- **Constraint Types**:
  - `FORBIDDEN_DEPENDENCY` - Prevent specific dependency patterns
  - `FORBIDDEN_TECHNOLOGY` - Block specific technologies
  - `REQUIRED_PATTERN` - Mandate labels/naming
  - `MAX_DEPENDENCY_DEPTH` - Limit graph depth

---

## 3. Core Actions & Business Logic

### Actions Module (`core/task_management/actions.py`)
Pure domain logic with no external dependencies:
- `create_issue_action()` - Validates, creates issues with component management
- `close_issue_action()` - Validates no open dependencies before closing
- `move_issue_action()` - Cross-component movement with validation
- `add_dependency_action()` - Cycle detection via BFS
- `remove_dependency_action()` - Graph edge removal
- `get_blocked_issues_action()` - Identifies work blockers
- `get_workable_issues_action()` - Finds ready-to-work issues
- `get_dependency_chain_action()` - Transitive dependency analysis
- `update_component_action()` - Component metadata updates
- `delete_component_action()` - Safe deletion with force flag

### Validation System (`core/validation/`)
- `input_sanitizer.py` - XSS prevention, HTML tag removal, control character stripping
- `validators.py` - Length limits, pattern matching, custom exceptions
- `exceptions.py` - Domain-specific validation errors

---

## 4. Analysis & Intelligence Engine

### Architectural Analyzer (`core/project_analysis/analyzer.py`)
```python
class ArchitecturalAnalyzer:
    - validate_issue_creation()      # Check before persist
    - validate_dependency()          # Prevent forbidden relationships
    - _check_forbidden_technology()  # Regex pattern matching
    - _check_required_pattern()      # Label enforcement
    - _check_frozen_dependency()     # Forbidden dependency rules
    - _check_max_depth()             # Graph depth limits
```

### Root Cause Analyzer (`core/project_analysis/analyzer.py`)
Advanced causal inference using:
- **Graph Proximity**: Direct dependencies, shared components
- **Temporal Analysis**: Recently closed issues as culprits
- **Semantic Matching**: Keyword overlap (excluding stop words)
- **Confidence Scoring**: Weighted combination of signals
- **Impact Analysis**: Transitive effect propagation through graph

### Rules System (`core/project_analysis/rules.py`)
- `ArchitecturalRule` - Configurable policies with severity levels
- `RuleType` - FORBIDDEN_DEPENDENCY, FORBIDDEN_TECHNOLOGY, REQUIRED_PATTERN, MAX_DEPENDENCY_DEPTH
- `Violation` - Structured rule violation reporting

---

## 5. Storage Layer (Neo4j Only)

### Repository Implementation (`storage/graph_database/repositories.py`)
- Implements `TaskRepositoryInterface` protocol
- Neo4j-specific queries using Cypher
- Transaction support via context manager
- All business logic in `core/`, storage only handles persistence

### Graph Schema
- **Nodes**: Issues, Components
- **Relationships**: `[:DEPENDS_ON]`, `[:BLOCKS]`, `[:AFFECTS]`
- **Properties**: Full issue metadata, timestamps, status, priority

---

## 6. CLI Interface (`entrypoints/terminal_cli/`)

### Command Structure
```
tasker [global options] <command> [args]

Commands:
├── issue create/list/show/close/move/delete/start/finish
├── dependency add/remove/list/chain/blocked
├── component create/list/show/update/delete
├── analyze root-cause/impact
├── project detect/setup
├── seed run
├── init <path>
├── status
└── [project] detect/setup
```

### Key Design Features
- **Partial ID Resolution**: Accepts 4+ character prefixes or partial UUIDs
- **Component Name Lookup**: Exact matches for short names
- **Rich Terminal UI**: Color-coded status/priority with custom themes
- **Error Handling**: User-friendly messages without stack traces
- **Global Options**: Neo4j connection via CLI flags or environment variables

---

## 7. API Interface (`entrypoints/web_api/`)

### FastAPI Application
- **Authentication**: Optional API key via `X-API-Key` header
- **Rate Limiting**: Configurable per-client request throttling
- **CORS**: Enabled for browser-based clients
- **OpenAPI Schema**: Auto-generated with `tags` for discoverability

### API Endpoints (`routes/` directory)
- `/api/v1/issues` - CRUD operations
- `/api/v1/dependencies` - Relationship management
- `/api/v1/components` - Component management
- `/api/v1/analysis/impact/{id}` - Impact analysis
- `/api/v1/analyze/root-cause/{id}` - Root cause suggestions
- `/api/v1/health` - Health check with Neo4j status
- `/api/v1/webhooks/github` - GitHub integration

### Middleware Stack
1. API Key Authentication (optional)
2. Rate Limiting (configurable)
3. Request/Response logging
4. Global exception handlers (structured error responses)

---

## 8. Testing Infrastructure

### Test Organization
```
tests/
├── conftest.py                  # Shared fixtures
├── unit/                        # Fast, isolated tests
│   ├── test_validation.py
│   ├── test_actions.py
│   ├── test_entities.py
│   └── ... (270+ tests)
└── integration/                 # Storage/API integration
    ├── test_neo4j_repository.py
    └── test_webhooks.py
```

### Testing Approach
- **Unit Tests**: Mock repositories, test pure domain logic
- **Integration Tests**: Real Neo4j instance (Docker)
- **Coverage**: Targeted at core logic, validation, and actions
- **Test Structure**: `Test{ClassName}` classes with `test_{behavior}` methods

---

## 9. Configuration & Environment

### Key Environment Variables
```
TASKER_NEO4J_URI           # Neo4j Bolt URL (default: bolt://localhost:7687)
TASKER_NEO4J_USER          # Username (default: neo4j)
TASKER_NEO4J_PASSWORD      # Required
TASKER_API_KEY             # Optional authentication
TASKER_AUTH_ENABLED        # Boolean (default: false)
TASKER_RATE_LIMIT          # Requests/minute (default: 100)
TASKER_RATE_LIMIT_ENABLED  # Boolean (default: false)
TASKER_NEO4J_DATABASE      # Database name
```

### Project Configuration
- `pyproject.toml` or `package.json` for project detection
- Docker Compose for multi-service projects
- Convention-based module discovery

---

## 10. Key Design Patterns

1. **Policy Enforcement** - Configurable architectural rules evaluated at action time
2. **Graph Traversal** - BFS for dependency chains, cycle detection
3. **Causal Inference** - Multi-factor root cause analysis (graph + temporal + semantic)
4. **Hexagonal Ports** - `TaskRepositoryInterface` decouples domain from storage
5. **Deterministic Actions** - All core functions are pure, testable, and side-effect-free
6. **Progressive Disclosure** - CLI for operations, API for integration
7. **Zero Placeholders** - All code is production-ready, no TODOs or FIXMEs

---

## 11. Project Capabilities

### What It Does
- **Task Management**: Create, organize, and track issues with dependencies
- **Architectural Governance**: Enforce design rules automatically
- **Root Cause Analysis**: Automatically suggest likely culprits for failures
- **Impact Assessment**: Predict downstream effects of changes
- **Multi-Storage Support**: Currently Neo4j-only, designed for extensibility
- **CI/CD Integration**: CLI and API for automation
- **Demo Data**: Pre-configured seed for quick evaluation

### What Makes It Unique
- **Graph-Native**: Relationships are first-class citizens, not afterthoughts
- **Agent-Ready**: Designed for autonomous AI agent coordination
- **Analysis-Focused**: Built-in causal reasoning, not just task tracking
- **Policy-Driven**: Architecture as code through configurable rules

---

## 12. File Organization Summary

### Core Domain (`src/socialseed_tasker/core/`)
- `task_management/entities.py` - Issue, Component, Agent entities
- `task_management/actions.py` - Core business logic actions
- `task_management/constraints.py` - Constraint domain models
- `task_management/value_objects.py` - ReasoningLogEntry, etc.
- `validation/` - Input sanitization and validation
- `project_analysis/` - Analyzer, rules, policy engine
- `services/` - External integrations

### Entrypoints (`src/socialseed_tasker/entrypoints/`)
- `terminal_cli/app.py` - Main CLI application
- `terminal_cli/commands.py` - All CLI command implementations
- `web_api/app.py` - FastAPI application factory
- `web_api/routes/` - API endpoint routers

### Storage (`src/socialseed_tasker/storage/`)
- `graph_database/driver.py` - Neo4j driver management
- `graph_database/repositories.py` - Repository implementations
- `graph_database/queries.py` - Cypher query definitions

### Configuration (`src/socialseed_tasker/bootstrap/`)
- `container.py` - Dependency injection container
- `wiring.py` - Application wiring

---

## 13. Development Workflow

1. **Issue Creation**: `tasker issue create "Title" -c component -p priority`
2. **Dependency Management**: `tasker dependency add issue --depends-on other`
3. **Analysis**: `tasker analyze root-cause <test-failure>` or `tasker analyze impact <issue>`
4. **Project Setup**: `tasker project setup` or `tasker project detect`
5. **Testing**: `python -m pytest tests/`

---

## 14. Quality Assurance

- **Code Review**: All changes require review
- **Testing**: 270+ unit tests, integration tests with real Neo4j
- **Linting**: Type checking, linting configured
- **Documentation**: Comprehensive docstrings, CLI help, API docs
- **Security**: Input validation, XSS prevention, parameterized queries

---

*Generated from comprehensive codebase analysis excluding temporary files and `.agent` directory*