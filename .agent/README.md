# Agent Skills & Workflows for SocialSeed Tasker

This directory contains the operational knowledge for AI agents working on this project.

## Directory Structure

```
.agent/
├── skills/          # Specialized capabilities and conventions
└── workflows/       # Step-by-step procedural guides
```

## Quick Reference

| Task | Workflow File |
|------|--------------|
| Implement an issue | `workflows/implement-issue.md` |
| Write and run tests | `workflows/test-code.md` |
| Commit and push | `workflows/commit-push.md` |
| Create a new issue | `workflows/create-issue.md` |
| Test project | `workflows/test-project.md` |
| Project setup | `workflows/project-setup.md` |
| **Prueba el proyecto** | `workflows/prueba-el-proyecto.md` |

## Core Principles

1. **Read project.md first**: Before any work, read `project.md` at the root to understand the project structure (see `skills/project-documentation.md`)
2. **Issue-driven development**: Every piece of work starts from an issue in `.issues/`
3. **Test before commit**: No code goes in without tests
4. **Documentation sync**: Always update docs when fixing issues (see `skills/documentation-sync.md`)
5. **Conventional commits**: Follow the established commit message format
6. **English only**: All code, comments, docs, and commit messages in English
7. **No placeholders**: Every line must be production-ready

## Project Information

| Attribute | Value |
|-----------|-------|
| Version | **0.9.0** |
| Storage | Neo4j only |
| Architecture | Hexagonal (Feature-Oriented) |
| Entry Points | CLI (Typer), REST API (FastAPI) |
| Branch | `main` |

## Key Features (v0.9.0)

- **Input Validation**: XSS and Neo4j injection prevention
- **API Authentication**: `TASKER_API_KEY` + `TASKER_AUTH_ENABLED`
- **Rate Limiting**: Configurable per-minute limits
- **Workable Issues**: Filter by status, priority, component
- **Impact Analysis**: Component and issue impact analysis
- **Project Dashboard**: Summary with dependency health metrics
- **Dependency Graph**: Full graph visualization endpoint
- **Code-as-Graph**: Tree-sitter powered code parsing to Neo4j graph

## CLI Commands

```bash
# Components
tasker component create <name> -p <project>
tasker component list
tasker component show <id>
tasker component update <id>
tasker component delete <id>

# Issues
tasker issue create <title> -c <component> -p <priority>
tasker issue list
tasker issue show <id>
tasker issue close <id>

# Dependencies
tasker dependency add <issue> --depends-on <dep>
tasker dependency chain <issue>
tasker dependency blocked
tasker dependency list

# Analysis
tasker analyze root-cause <issue>
tasker analyze impact <issue>

# Seed
tasker seed run

# Init (scaffold)
tasker init <path>
tasker init <path> --force

# Code-as-Graph (v0.9.0)
tasker code-graph scan <path> --incremental
tasker code-graph find <name>
tasker code-graph files
tasker code-graph stats
tasker code-graph clear
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check with Neo4j status |
| `/api/v1/components` | GET/POST | CRUD for components |
| `/api/v1/issues` | GET/POST | CRUD for issues (paginated) |
| `/api/v1/issues/{id}` | GET/PATCH/DELETE | Single issue operations |
| `/api/v1/issues/{id}/close` | POST | Close an issue |
| `/api/v1/issues/{id}/dependencies` | GET/POST | Dependency CRUD |
| `/api/v1/workable-issues` | GET | Issues ready to work on |
| `/api/v1/analyze/impact/{id}` | GET | Impact analysis |
| `/api/v1/analyze/component-impact/{id}` | GET | Component impact |
| `/api/v1/projects/{name}/summary` | GET | Project dashboard |
| `/api/v1/graph/dependencies` | GET | Dependency graph |
| `/api/v1/admin/reset` | POST | Reset data |
| `/api/v1/sync/status` | GET | Sync status |
| `/api/v1/sync/queue` | GET | Sync queue |
| `/api/v1/webhooks/github/test` | GET | Webhook test |
| `/api/v1/code-graph/scan` | POST | Scan repository to graph |
| `/api/v1/code-graph/files` | GET | List files in graph |
| `/api/v1/code-graph/symbols` | GET | Query code symbols |
| `/api/v1/code-graph/stats` | GET | Code graph statistics |
| `/api/v1/code-graph` | DELETE | Clear code graph data |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_NEO4J_URI` | `bolt://localhost:7687` | Neo4j URI |
| `TASKER_NEO4J_USER` | `neo4j` | Neo4j user |
| `TASKER_NEO4J_PASSWORD` | - | Neo4j password (required) |
| `API_PORT` | `8000` | API port |
| `TASKER_API_KEY` | - | API authentication key |
| `TASKER_AUTH_ENABLED` | `false` | Enable auth |
| `TASKER_DEMO_MODE` | `false` | Load demo data |
| `TASKER_RATE_LIMIT` | `100` | Requests/minute |

## Testing Commands

```bash
# Install dependencies
.venv/Scripts/pip.exe install -e .

# Run all tests
.venv/Scripts/python.exe -m pytest tests/ -v

# Run unit tests
.venv/Scripts/python.exe -m pytest tests/unit/ -v

# Run with coverage
.venv/Scripts/python.exe -m pytest tests/ --cov=socialseed_tasker --cov-report=term-missing
```

## Docker Commands

```bash
# Start all services
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f tasker-api

# Stop (data persists)
docker compose down

# Stop and remove data
docker compose down -v
```

## Complete Feature Reference

| Feature | Status | Issue |
|---------|--------|-------|
| Graph-Only Storage | ✅ | # |
| Agent Working Indicator | ✅ | # |
| Root Cause Analysis | ✅ | # |
| Impact Analysis | ✅ | # |
| CLI + REST API | ✅ | # |
| Project Scaffolding | ✅ | # |
| Workable Issues | ✅ | #65 |
| Component Impact | ✅ | #68 |
| API Authentication | ✅ | #69, #107 |
| Rate Limiting | ✅ | #108 |
| Graph Dependencies | ✅ | #70 |
| Project Dashboard | ✅ | #72 |
| GitHub Adapter | ✅ | #88 |
| Webhook Listener | ✅ | #89 |
| Causal Mirroring | ✅ | #90 |
| Offline-First Sync | ✅ | #91, #94 |
| Webhook Validator | ✅ | #95 |
| Markdown Transformer | ✅ | #96 |
| Secret Manager | ✅ | #97 |
| AI Reasoning Logs | ✅ | #78 |
| Live Agent Docs | ✅ | #79 |
| Agent Lifecycle | ✅ | #81 |
| Policy Enforcement | ✅ | #82 |
| Constraints System | ✅ | #126 |
| Code-as-Graph | ✅ | #208 |

## Skills Reference

See `.agent/skills/` for detailed architecture and workflow documentation.

### Real-Test Evaluation Skills
| Skill | Purpose |
|-------|---------|
| `terminal.md` | Docker, venv, shell management |
| `api-client.md` | REST API interaction for black-box testing |
| `reporter.md` | Report generation in YAML format |

### Test Profiles (Real-Test)
| Profile | Behavior |
|---------|----------|
| Junior Dev | Relies on documentation, reports "Doc Gaps" |
| Senior Architect | Focuses on graph efficiency, reports refactoring |
| DevOps | Focuses on infrastructure, logs, Docker stability |
| Chaos Monkey | Uses ONLY `--help` + error messages |

## Full Documentation

- `README.md` - Main project documentation
- `API_REFERENCE.md` - Complete API endpoint reference
- `VERSIONS.md` - Release milestones and checkboxes