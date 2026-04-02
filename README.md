# SocialSeed Tasker

A graph-based task management framework designed to provide "Infinite Context" and "Architectural Governance" to AI agents.

## Overview

SocialSeed Tasker transforms traditional task management by treating relationships between tasks as first-class citizens in a graph database. This enables powerful capabilities like architectural integrity checking, causal traceability (linking failed tests to root causes), and intelligent dependency management.

The framework implements a **Feature-Oriented Hexagonal Architecture** ensuring clean separation of concerns:
- **Core**: Pure Python business logic (no external dependencies)
- **Entry Points**: CLI and API interfaces
- **Storage**: Neo4j graph database with local file fallback
- **Bootstrap**: Dependency injection and system wiring

## Key Features

### 🔗 Dependency Graphing
Tasks support rich relationships:
- `[:DEPENDS_ON]` - Task requires completion of another task
- `[:BLOCKS]` - Task prevents another task from starting
- `[:AFFECTS]` - Task influences another task (weaker than blocks)

### 🏗️ Architectural Integrity
Verify actions against established architectural rules:
- Prevent forbidden dependencies between components
- Enforce required patterns (e.g., "All API changes must have tests")
- Limit technology usage in specific components
- Control dependency chain depth

### 🔍 Causal Traceability
Link failed tests to recently closed issues to find root causes:
- Graph proximity analysis to identify likely culprits
- Temporal proximity weighting (recent changes more suspect)
- Component overlap analysis
- Semantic similarity matching

### 💾 Dual Storage
Choose your persistence layer:
- **Neo4j**: Full graph capabilities for production
- **Local Files**: JSON-based fallback for development/testing

### 🖥️ Multiple Interfaces
- **CLI**: Terminal interface for humans and scripts
- **REST API**: Programmatic access for AI agents and external tools

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Docker & Docker Compose (for Neo4j)
- Git

### Installation

#### Option 1: Development Installation (Recommended)
```bash
# Clone the repository
git clone https://github.com/daironpf/socialseed-tasker.git
cd socialseed-tasker

# Install in development mode with all extras
pip install -e ".[dev]"

# Start Neo4j database
docker compose up -d

# Verify installation
tasker --help
```

#### Option 2: Production Installation
```bash
# Install from PyPI (when available)
pip install socialseed-tasker

# Configure environment variables (see Configuration section)
```

### Quick Start Guide

#### 1. Initialize Your Project

```bash
# Create a component (logical grouping of related tasks)
tasker component create --name "Backend" --project "my-project" \
    --description "Backend services and APIs"

# Create another component
tasker component create --name "Frontend" --project "my-project" \
    --description "User interface and client-side code"
```

#### 2. Create and Manage Issues

```bash
# Create a new issue
tasker issue create --title "Implement user authentication API" \
    --component <backend-component-id> \
    --priority HIGH \
    --description "Create login/logout endpoints with JWT validation" \
    --labels backend,api,security

# List all issues
tasker issue list

# Show detailed information about an issue
tasker issue show <issue-id>

# Create related issues
tasker issue create --title "Create login UI component" \
    --component <frontend-component-id> \
    --priority MEDIUM \
    --description "Build React login form with validation" \
    --labels frontend,ui,auth
```

#### 3. Manage Dependencies

```bash
# Make frontend task depend on backend API completion
tasker dependency add <frontend-issue-id> <backend-issue-id>

# View dependency chain for an issue
tasker dependency chain <issue-id>

# Check for blocked issues (those waiting on open dependencies)
tasker dependency blocked

# Remove a dependency when requirements change
tasker dependency remove <issue-id> <depends-on-id>
```

#### 4. Work with Components

```bash
# List all components
tasker component list

# Show details of a specific component
tasker component show <component-id>

# List issues within a component
tasker issue list --component <component-id>
```

#### 5. Use the API Interface

```bash
# Start the API server
uvicorn socialseed_tasker.entrypoints.web_api.app:app --reload

# Access the interactive documentation
# Open: http://localhost:8000/docs
# Alternative: http://localhost:8000/redoc

# Example API usage with curl:
curl -X 'POST' \
  'http://localhost:8000/api/v1/issues/' \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "API Health Check Endpoint",
    "description": "Add a simple health check endpoint",
    "component_id": "<component-id>",
    "priority": "LOW",
    "labels": ["api", "monitoring"]
  }'
```

## Architecture Deep Dive

### Hexagonal Architecture (Ports and Adapters)

```
                          ┌─────────────────────┐
                          │  Entry Points (API) │
                          │  Entry Points (CLI) │
                          └─────────┬───────────┘
                                    ▼
                    ┌─────────────────────────┐
                    │   Application Core      │
                    │  (Business Logic)       │
                    │                         │
                    │  • Issue Management     │
                    │  • Dependency Rules     │
                    │  • Architectural Rules  │
                    │  • Validation Engines   │
                    └─────────┬───────────────┘
                              ▼
          ┌─────────────────────┐   ┌─────────────────────┐
          │ Storage Adapters    │   │ Storage Adapters    │
          │ (Neo4j Backend)     │   │ (File System Backend)│
          └─────────────────────┘   └─────────────────────┘
```

### Core Principles

1. **Pure Python Core**: Zero external framework dependencies in `core/` directory
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Interface Segregation**: Small, specific interfaces rather than large monolithic ones
4. **Testability**: Core logic can be tested without databases or web frameworks

## Configuration

All configuration is done through environment variables. Create a `.env` file or set variables in your environment:

### Storage Configuration
| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TASKER_STORAGE_BACKEND` | Storage backend (`neo4j` or `file`) | `neo4j` | No |
| `TASKER_NEO4J_URI` | Neo4j connection string | `bolt://localhost:7687` | Yes (if using neo4j) |
| `TASKER_NEO4J_USER` | Neo4j username | `neo4j` | Yes (if using neo4j) |
| `TASKER_NEO4J_PASSWORD` | Neo4j password | *(required)* | Yes (if using neo4j) |

### API Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `TASKER_API_HOST` | API bind address | `0.0.0.0` |
| `TASKER_API_PORT` | API port | `8000` |
| `TASKER_API_RELOAD` | Enable auto-reload (dev only) | `false` |

### Example `.env` File
```bash
# Storage Backend
TASKER_STORAGE_BACKEND=neo4j
TASKER_NEO4J_URI=bolt://localhost:7687
TASKER_NEO4J_USER=neo4j
TASKER_NEO4J_PASSWORD=your_secure_password_here

# API Server
TASKER_API_HOST=0.0.0.0
TASKER_API_PORT=8000
TASKER_API_RELOAD=false
```

## Development Workflow

### Running Tests
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test module
pytest tests/unit/test_analyzer.py -v

# Run tests matching a pattern
pytest -k "test_analyzer" -v
```

### Code Quality Checks
```bash
# Run linting
ruff check .

# Run linting with auto-fix
ruff check --fix .

# Run type checking
mypy .

# Run tests with coverage
pytest --cov=socialseed_tasker --cov-report=term-missing
```

### Database Management
```bash
# Start Neo4j with Docker Compose
docker compose up -d

# Stop Neo4j
docker compose down

# View Neo4j logs
docker compose logs -f neo4j

# Access Neo4j Browser UI
# Open: http://localhost:7474
# Login with your neo4j credentials
```

## Advanced Usage

### Architectural Integrity Rules

The system includes built-in rule types for enforcing architectural constraints:

#### Rule Types
- `FORBIDDEN_DEPENDENCY`: Prevents issues in one component from depending on another
- `FORBIDDEN_TECHNOLOGY`: Prevents certain technologies in specific components  
- `REQUIRED_PATTERN`: Requires issues to follow specific patterns (labels, etc.)
- `MAX_DEPENDENCY_DEPTH`: Limits how deep dependency chains can go

#### Example: Creating Architectural Rules
```python
# This would typically be done through the API or CLI extensions
from socialseed_tasker.core.project_analysis.analyzer import ArchitecturalAnalyzer
from socialseed_tasker.core.project_analysis.rules import ArchitecturalRule, RuleType, Severity
from socialseed_tasker.core.task_management.actions import TaskRepositoryInterface

# Initialize analyzer with repository
analyzer = ArchitecturalAnalyzer(repository: TaskRepositoryInterface)

# Create a forbidden dependency rule
rule = ArchitecturalRule(
    name="UI-Database Separation",
    description="UI components cannot depend directly on Database components",
    rule_type=RuleType.FORBIDDEN_DEPENDENCY,
    source_pattern="ui-component-id-here",
    target_pattern="database-component-id-here",
    severity=Severity.ERROR
)

# Register the rule
analyzer.add_rule(rule)

# Validate an issue creation against all rules
validation_result = analyzer.validate_issue_creation(new_issue)
if not validation_result.is_valid:
    for violation in validation_result.violations:
        print(f"Rule Violation: {violation.message}")
        print(f"Suggestion: {violation.suggestion}")
```

### Causal Traceability & Root Cause Analysis

When integrated with test execution systems (like `socialseed-e2e`), the framework can:

1. Automatically detect test failures
2. Analyze recently closed issues in related components
3. Calculate proximity scores based on:
   - Graph distance (shorter paths = higher suspicion)
   - Temporal recency (recent changes weighted higher)
   - Component overlap (same component = strong signal)
   - Semantic similarity (keyword/description matching)
4. Return ranked list of potential root causes with explanations

## Extending the Framework

### Adding New CLI Commands

1. Add new command functions in `src/socialseed_tasker/entrypoints/terminal_cli/commands.py`
2. Register them with the appropriate Typer Typer group
3. Follow the existing pattern: delegate to core actions, handle presentation only

### Adding New Storage Backends

1. Implement `TaskRepositoryInterface` from `src/socialseed_tasker/core/task_management/actions.py`
2. Add your implementation to the `storage/` directory
3. Update the bootstrap container to conditionally use your backend
4. No changes needed to core logic thanks to dependency injection

### Adding New API Endpoints

1. Define Pydantic models in `src/socialseed_tasker/entrypoints/web_api/schemas.py`
2. Add route handlers in `src/socialseed_tasker/entrypoints/web_api/routes.py`
3. Register routes in `src/socialseed_tasker/entrypoints/web_api/app.py`
4. Follow existing patterns for dependency injection and error handling

## Design Decisions

### Why Neo4j?
- Native graph storage and traversal algorithms
- ACID transactions for data integrity
- Mature ecosystem and tooling
- Cypher query language optimized for graph patterns

### Why Hexagonal Architecture?
- Independent evolution of core logic and infrastructure
- Easy testing with mock adapters
- Clear boundaries between concerns
- Ability to swap implementations (Neo4j ↔ File storage)

### Why Pure Python Core?
- Framework independence and testability
- Reduced coupling to specific libraries/vendors
- Easier to reason about and maintain
- Faster test execution

## Contributing

See `CONTRIBUTING.md` for detailed guidelines on:
- Setting up development environment
- Coding standards and conventions
- Pull request process
- Testing requirements

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built as part of the [SocialSeed Project](https://github.com/daironpf/SocialSeed)
- Inspired by Domain-Driven Design and Hexagonal Architecture principles
- Thanks to all contributors and users who help improve this framework