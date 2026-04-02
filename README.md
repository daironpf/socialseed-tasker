# SocialSeed Tasker

A graph-based task management framework designed to provide "Infinite Context" and "Architectural Governance" to AI agents.

## Features

- **Dependency Graphing**: Tasks support [:DEPENDS_ON], [:BLOCKS], and [:AFFECTS] relationships
- **Architectural Integrity**: Verify actions against established architectural rules
- **Causal Traceability**: Link failed tests to recently closed issues to find root causes
- **Dual Storage**: Neo4j graph database or local file fallback
- **CLI & API**: Terminal interface for humans, REST API for AI agents

## Quick Start

### Prerequisites

- Python 3.10+
- Docker & Docker Compose

### Installation

```bash
# Install the package
pip install -e ".[dev]"

# Start Neo4j
docker compose up -d

# Run the CLI
tasker --help
```

### Basic Usage

```bash
# Create a component
tasker component create --name "Backend" --project "my-project"

# Create an issue
tasker issue create --title "Fix login bug" --component <id> --priority HIGH

# Add a dependency
tasker dependency add <issue_id> <depends_on_id>

# Check blocked issues
tasker dependency blocked
```

### API Usage

```bash
# Start the API server
uvicorn socialseed_tasker.entrypoints.web_api.app:app --reload

# View OpenAPI docs
open http://localhost:8000/docs
```

## Architecture

This project follows a **Hexagonal Architecture** organized by **Functional Features**:

- **core/**: Pure Python business logic, no external dependencies
- **entrypoints/**: CLI (Typer) and API (FastAPI) interfaces
- **storage/**: Neo4j and local file storage backends
- **bootstrap/**: Dependency injection and system wiring

## Configuration

All configuration via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| TASKER_STORAGE_BACKEND | Storage backend (neo4j/file) | neo4j |
| TASKER_NEO4J_URI | Neo4j connection string | bolt://localhost:7687 |
| TASKER_NEO4J_USER | Neo4j username | neo4j |
| TASKER_NEO4J_PASSWORD | Neo4j password | (required) |
| TASKER_API_HOST | API bind address | 0.0.0.0 |
| TASKER_API_PORT | API port | 8000 |

## Development

```bash
# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy .
```

## License

Apache 2.0 - See LICENSE file for details.