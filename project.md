# SocialSeed Tasker - Project Overview

## Project Summary

**SocialSeed Tasker** (v0.8.0) is a graph-based task management framework for AI agents with Neo4j storage backend, hexagonal architecture, and comprehensive tooling for CLI and API interfaces.

```
┌─────────────────────────────────────────────────────────────────────────────────────┐
│                     TASKER v0.8.0                              │
├────────────────────────────────────────────────────────────────────────────┬─────────────────┤
│  CLI (Typer)    │    API (FastAPI)    │    Skills (Python)    │  Neo4j  │
│  tasker issue   │    /api/v1/issues  │    task_skill.py     │  Graph │
│  tasker status  │    /projects/sum   │    Quality Guide    │   DB   │
└─────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Architecture

### Package Structure
```
src/socialseed_tasker/
├── core/                          # Domain logic (no external deps)
│   ├── task_management/             # Entities, actions, constraints
│   ├── project_analysis/          # Rules, analyzers, policies
│   ├── validation/               # Input sanitization
│   ├── services/                # External integrations
│   └── system_init/              # Scaffolding
├── entrypoints/                   # External interfaces
│   ├── terminal_cli/              # Typer CLI (tasker)
│   ├── web_api/                 # FastAPI REST API
│   └── cli/                     # Init command
├── storage/                       # Neo4j persistence
├── bootstrap/                    # DI container
└── assets/                      # Templates & skills
    └── templates/
        ├── skills/              # AI Agent skill functions
        └── frontend/            # Vue Kanban board
```

---

## 2. Domain Model

### Issue Entity
```python
class Issue:
    id: UUID
    title: str (max 200)
    description: str
    status: IssueStatus  # OPEN, IN_PROGRESS, BLOCKED, CLOSED
    priority: IssuePriority  # LOW, MEDIUM, HIGH, CRITICAL
    component_id: UUID
    labels: list[str]
    dependencies: list[UUID]  # [:DEPENDS_ON]
    blocks: list[UUID]       # [:BLOCKS]
    affects: list[UUID]      # [:AFFECTS]
    agent_working: bool
    reasoning_logs: list[ReasoningLogEntry]
```

### Component Entity
```python
class Component:
    id: UUID
    name: str
    description: str | None
    project: str
```

### Constraint System
- **Categories**: ARCHITECTURE, TECHNOLOGY, NAMING, PATTERNS, DEPENDENCIES
- **Levels**: HARD (blocks), SOFT (warnings)
- **Types**: FORBIDDEN_DEPENDENCY, FORBIDDEN_TECHNOLOGY, REQUIRED_PATTERN, MAX_DEPENDENCY_DEPTH

---

## 3. Core Actions

### Domain Actions (`core/task_management/actions.py`)
- `create_issue_action()` - Create with validation
- `close_issue_action()` - Validate no open dependencies
- `move_issue_action()` - Cross-component movement
- `add_dependency_action()` - Cycle detection (BFS)
- `remove_dependency_action()` - Edge removal
- `get_blocked_issues_action()` - Identify blockers
- `get_workable_issues_action()` - Ready to work
- `get_dependency_chain_action()` - Transitive analysis
- `get_dependency_graph_action()` - Full graph
- `analyze_impact_action()` - Downstream effects

### Analysis Engine (`core/project_analysis/`)
- **ArchitecturalAnalyzer**: Rule enforcement at creation time
- **RootCauseAnalyzer**: Graph + temporal + semantic inference
- **ImpactAnalyzer**: Transitive effect propagation

---

## 4. Storage Layer

### Neo4j Repository
```python
class Neo4jTaskRepository:
    - Implements TaskRepositoryInterface
    - Uses Cypher queries
    - Full CRUD + relationships
    - Cycle detection
```

### Graph Schema
- **Nodes**: Issue, Component
- **Rel**: DEPENDS_ON, BLOCKS, AFFECTS, BELONGS_TO

---

## 5. CLI Interface

### Commands
```
tasker [global options] <command>

Global Options:
  --neo4j-uri URI      # bolt://localhost:7687
  --neo4j-user USER   # neo4j
  --neo4j-password PW # Required
  --api-key KEY      # Optional auth

Commands:
├── issue
│   ├── create "title" -c COMP -p PRIORITY
│   ├── list [--status OPEN|CLOSED]
│   ├── show ID
│   ├── close ID
│   ├── move ID --to COMP
│   ├── delete ID
│   ├── start ID
│   └── finish ID
├── dependency
│   ├── add ID --depends-on OTHER
│   ├── remove ID --from OTHER
│   ├── list ID
│   ├── chain ID
│   └── blocked
├── component
│   ├── create NAME -p PROJECT
│   ├── list [--project P]
│   ├── show NAME
│   ├── update NAME [--name N] [--desc D]
│   └── delete NAME
├── analyze
│   ├── root-cause ISSUE
│   └── impact ISSUE
├── project
│   ├── detect
│   └── setup
├── seed run
├── init PATH
├── status           # Graph health dashboard
├── login
└── logout
```

### Enhanced Status Command
```bash
$ tasker status
┌────────────────────┐
│ Tasker Status     │
├────────────────────┤
Components: 5
Total Issues: 42
Dependencies: 15
Ready to Work: 12
Blocked: 3
...
```

---

## 6. API Interface

### Endpoints
```
/api/v1/
├── issues
│   ├── POST /              # Create
│   ├── GET /              # List (filter: status, component, project)
│   ├── GET /{id}          # Get
│   ├── PUT /{id}          # Update
│   ├── DELETE /{id}       # Delete
│   └── POST /{id}/close   # Close (validates deps)
├── components
│   ├── POST /              # Create
│   ├── GET /              # List
│   ├── GET /{id}          # Get
│   ├── PUT /{id}          # Update
│   └── DELETE /{id}       # Delete
├── issues/{id}/dependencies
│   ├── POST /              # Add dependency
│   ├── GET /              # List dependencies
│   └── DELETE /{id}       # Remove
├── issues/{id}/dependents
│   └── GET /              # Issues depending on this
├── dependencies
│   ├── GET /graph         # Full graph
│   └── GET /blocked      # Blocked issues
├── analysis
│   ├── /impact/{id}       # Impact analysis
│   └── /root-cause/{id}   # Root cause suggestions
├── projects/{name}/summary
│   └── GET /              # Project dashboard
├── health
│   └── GET /              # Health check
└── webhooks
    └── /github            # GitHub integration
```

### Middleware
1. API Key Authentication (optional)
2. Rate Limiting (configurable)
3. CORS enabled
4. Structured error responses

---

## 7. AI Agent Skills

### Skill Functions (`assets/templates/skills/`)
```python
# Components
create_component(name, project, description, labels)
list_components(project, name)
get_component(component_id)
update_component(component_id, updates)
delete_component(component_id)

# Issues
create_issue(title, component_id, priority, description, labels)
list_issues(status, component, project)
get_issue(issue_id)
update_issue(issue_id, updates)
close_issue(issue_id)
delete_issue(issue_id)
get_workable_issues()

# Dependencies
add_dependency(issue_id, depends_on_id)
remove_dependency(issue_id, depends_on_id)
get_dependencies(issue_id)
get_dependency_chain(issue_id)
get_blocked_issues()
get_dependency_graph()

# Analysis
analyze_impact(issue_id)
analyze_component_impact(component_id)
analyze_root_cause(failure_description)

# Dashboard
get_project_summary(project_name)

# System
health_check()
admin_reset(scope)
```

### Quality Guide (`issue_quality_guide.json`)
Standards for agent-created issues:
- **Title Format**: `[Component] Action: Expected Result`
- **Description**: Context + Acceptance Criteria + Technical Notes
- **Priority Guide**: CRITICAL/HIGH/MEDIUM/LOW with examples
- **Dependency Guide**: When and how to create dependencies

---

## 8. Testing

### Test Suite
```
tests/
├── conftest.py           # Shared fixtures
├── unit/               # 429 tests
│   ├── test_cli_commands.py
│   ├── test_api.py
│   ├── test_actions.py
│   ├── test_entities.py
│   ├── test_repositories.py
│   └── ...
└── integration/        # Neo4j tests
    ├── test_neo4j_repository.py
    └── test_webhooks.py
```

### Test Results
```
429 passed, 0 failed
```

---

## 9. Configuration

### Environment Variables
```
TASKER_NEO4J_URI           # bolt://localhost:7687
TASKER_NEO4J_USER          # neo4j
TASKER_NEO4J_PASSWORD      # Required
TASKER_NEO4J_DATABASE      # neo4j
TASKER_API_KEY             # Optional
TASKER_AUTH_ENABLED       # false
TASKER_RATE_LIMIT         # 100/min
TASKER_RATE_LIMIT_ENABLED # false
```

---

## 10. Docker Services

### docker-compose.yml
```yaml
services:
  tasker-db:      # Neo4j
  tasker-api:     # FastAPI
  tasker-board:  # Vue Kanban
```

### Ports
- Neo4j Browser: http://localhost:7474
- REST API: http://localhost:8000
- Frontend: http://localhost:8080

---

## 11. Key Features (v0.8.0)

| Feature | Status |
|--------|--------|
| Graph-based task management | ✅ |
| Hexagonal architecture | ✅ |
| CLI with Rich UI | ✅ |
| REST API | ✅ |
| AI Agent skills | ✅ |
| Quality guide for agents | ✅ |
| Dependency graph visualization | ✅ |
| Root cause analysis | ✅ |
| Impact analysis | ✅ |
| Architectural constraints | ✅ |
| GitHub sync | ✅ |
| Vue Kanban board | ✅ |

---

## 12. Development

### Quick Start
```bash
# Install
pip install socialseed-tasker

# Start services
docker compose up -d

# Initialize project
tasker init .
tasker login --password neoSocial

# Create issues
tasker issue create "Fix auth bug" -c backend -p HIGH
```

### Running Tests
```bash
pytest tests/unit/ -v
```

---

## 13. CI/CD

### GitHub Actions
- Auto-publish to PyPI on version tags
- Docker image build & push
- GitHub release creation
- PyPI verification

### Publishing
```bash
git tag v0.8.0
git push origin v0.8.0
```

---

*Generated: 2026-04-26*