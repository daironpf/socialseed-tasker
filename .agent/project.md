# SocialSeed Tasker

## AI Agent Project Context

This file provides essential context for AI agents working on this project. Agents should read this file when starting work to understand the project architecture and constraints.

**Version**: 1.0.0
**Created**: 2026-05-05
**Architecture**: Hexagonal (Feature-Oriented)
**Project Model**: Single Project (one project per Tasker instance)

---

## Single Project Rule

**Tasker supports only ONE project per instance.** This is a core architectural decision. All issues, components, agents, and code symbols belong to this single project. When registering an agent, it is automatically assigned to the existing project via the `(Project)-[:ASSIGNED_TO]->(Agent)` relationship.

---

## Architecture

### Type
```
Hexagonal (Feature-Oriented)
```

### Stack
- **Language**: Python
- **Framework**: FastAPI (API), Typer (CLI)
- **Database**: Neo4j
- **Frontend**: Vue.js (Kanban Board)
- **Other Services**: Neo4j, Tree-sitter, OpenAI (RAG)

### Key Components
- `core/task_management/` - Issue/Component entities and actions
- `core/project_analysis/` - Analyzers (impact, root-cause, architectural)
- `core/validation/` - Input sanitization
- `core/code_analysis/` - Tree-sitter code parsing
- `entrypoints/terminal_cli/` - Typer CLI (tasker)
- `entrypoints/web_api/` - FastAPI REST API
- `storage/graph_database/` - Neo4j repositories
- `application/` - Use cases, ports (Protocols), repository interfaces
- `infrastructure/` - Neo4j adapters, parsers, repository implementations
- `cli/` - Thin CLI entrypoint with argparse and DI wiring

---

## Communication

### GitHub
- **Repository**: (Not configured - add your repo)
- **Default Branch**: main

### External APIs
None currently configured

---

## Constraints

### Forbidden Technologies
- File storage (Neo4j-only)
- External databases in `core/` layer
- Direct Neo4j imports in `core/`

### Required Patterns
- Hexagonal Architecture (core/entrypoints/storage separation)
- Repository Pattern via Protocol interfaces
- All code in English

### Naming Conventions
- Python: snake_case for functions/variables, PascalCase for classes
- Components: kebab-case

### Dependency Rules
- No circular dependencies
- Max dependency depth: 5

---

## Development

### Setup Commands
```bash
# Start database
cd .agent && docker compose up -d

# Configure environment
cp .agent/configs/.env.example .agent/configs/.env
# Edit .env with your Neo4j password

# Install package
pip install -e .

# Run tests
pytest tests/unit/ tests/domain/ tests/application/ -v
```

### Testing
```bash
# Unit + domain + application tests
pytest tests/unit/ tests/domain/ tests/application/ -v

# With coverage
pytest tests/unit/ tests/domain/ tests/application/ --cov=socialseed_tasker --cov-report=term-missing

# Integration tests (requires Neo4j running)
pytest tests/integration/ -v -m integration

# Specific test file
pytest tests/domain/test_impact_analysis.py -v
```

### CI Pipeline
The project includes a GitHub Actions CI workflow (`.github/workflows/ci.yml`) that runs on every push and PR:
- **lint**: ruff, black --check, isort --check-only (Python 3.10, 3.11, 3.12)
- **typecheck**: mypy src/ (Python 3.10, 3.11, 3.12)
- **unit-tests**: pytest with `-k "not integration"` (Python 3.10, 3.11, 3.12)
- **integration-tests**: pytest `-m integration` with Neo4j service (optional, trigger with `integration=true` input)

### Build
```bash
pip install -e .
pip wheel . --wheel-dir dist/
```

---

## Quality Standards

### Issue Quality Requirements
- All issues must have clear acceptance criteria
- Use issue_quality_guide.json for reference
- Include technical notes for complex issues

### Code Review
- Require 1 approval(s) before merge
- All tests must pass
- Linting must pass

---

## Agent Protocol

### Interaction Guide
All AI agents MUST follow the protocol defined in [AGENT_GUIDE.md](./AGENT_GUIDE.md).

### Documentation Requirements
- Update `ROADMAP.md` when issues are resolved.
- Update `VERSIONS.md` when milestones are reached.
- Log architectural decisions using `tasker reasoning log`.

---

## Notes for Agents

### Important Notes
- Read `.agent/AGENT_GUIDE.md` before starting any task
- Register agent with Tasker before working on issues
- Log all reasoning decisions using `tasker reasoning log`
- Update code-graph after any code changes

### Do's and Don'ts
- DO: Use Neo4j for all persistence
- DO: Keep `core/` layer free of external dependencies
- DON'T: Import neo4j/fastapi/typer in core/ layer
- DON'T: Create issues without acceptance criteria

---

*This file is managed by SocialSeed Tasker. Do not edit manually unless necessary.*