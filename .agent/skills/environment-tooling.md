# Skill: Environment & Tooling

## Description

This project's development environment, tools, and conventions that all agents must know.

## Python Environment

- **Virtual env**: `.venv/` (Windows)
- **Python version**: 3.10+
- **Package manager**: pip (via `.venv/Scripts/pip.exe`)
- **Test runner**: pytest
- **Version**: 0.8.0

### Common Commands

```bash
# Install package in development mode
.venv/Scripts/pip.exe install -e .

# Install a package
.venv/Scripts/pip.exe install <package>

# Run all tests
.venv/Scripts/python.exe -m pytest tests/ -v

# Run specific test file
.venv/Scripts/python.exe -m pytest tests/unit/test_entities.py -v

# Run with coverage
.venv/Scripts/python.exe -m pytest tests/ --cov=socialseed_tasker --cov-report=term-missing

# Run Python with src in path
.venv/Scripts/python.exe -c "import sys; sys.path.insert(0, 'src'); ..."
```

## Docker / Neo4j

```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d tasker-api

# Stop services (data persists)
docker compose down

# Stop and remove data
docker compose down -v

# Check status
docker compose ps

# View logs
docker compose logs -f tasker-api

# View Neo4j logs
docker compose logs -f tasker-db
```

## Neo4j Configuration (Docker)

- Custom ports: HTTP=7474, Bolt=7687
- APOC plugin enabled
- Credentials: `neo4j` / `neoSocial`
- Data persists in Docker volume

## Git Conventions

- Branch: `main`
- Remote: `origin` (GitHub)
- `.issues/` directory is gitignored (issues are local tracking only)
- Conventional commits: `type: description`

## Commit Message Types

| Type | When to Use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `test` | Adding or fixing tests |
| `docs` | Documentation changes |
| `chore` | Maintenance tasks |
| `refactor` | Code restructuring without behavior change |

## File Conventions

- All code, comments, docstrings in **English**
- Line endings: LF (git auto-converts on Windows)
- Max line length: 120 characters
- No AI-generated placeholders
- No emojis in code or commit messages

## Project Structure Quick Reference

```
src/socialseed_tasker/
├── core/                      # Pure Python business logic
│   ├── task_management/        # Entities, actions
│   ├── project_analysis/       # Analyzers
│   ├── validation/           # Input validators
│   └── services/             # Webhook, Markdown, Secret managers
├── entrypoints/               # External interfaces
│   ├── terminal_cli/         # Typer CLI
│   └── web_api/             # FastAPI REST API
├── storage/                  # Storage backends
│   └── graph_database/       # Neo4j implementation (ONLY storage)
├── bootstrap/               # Dependency injection
└── assets/                 # Templates for scaffolding
tests/
├── unit/                    # Unit tests
└── integration/            # Integration tests
.agent/                    # AI agent skills and workflows
.issues/                  # Issue tracking (local, gitignored)
.issues/done/              # Completed issues
```

## New v0.8.0 CLI Commands

```bash
# Init (scaffold external project)
tasker init <path>
tasker init <path> --force

# Seed demo data
tasker seed run

# Constraints
tasker constraints list
tasker constraints set
tasker constraints validate

# Sync
tasker sync status
tasker sync force
```

## GitHub Integration (v0.8.0)

```bash
# Environment variables needed:
# GITHUB_TOKEN=ghp_...
# GITHUB_REPO=owner/repo
# GITHUB_WEBHOOK_SECRET=...

# API endpoints:
# POST /api/v1/webhooks/github
# GET /api/v1/webhooks/github/test
# GET /api/v1/sync/status
# GET /api/v1/sync/queue
# POST /api/v1/sync/force
```

## Version Information

| Component | Version |
|-----------|---------|
| Project | **0.8.0** |
| Storage | Neo4j only |
| Python | 3.10+ |
| CLI | tasker |
| API Base | /api/v1 |
| Tests | 270+ passing |