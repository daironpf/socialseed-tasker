# Agent Skills & Workflows

This directory contains the operational knowledge for AI agents working on this project.

## Directory Structure
```
.agent/
├── skills/          # Specialized capabilities (API interaction, impact analysis)
├── workflows/       # Step-by-step procedural guides
├── configs/         # Environment configuration templates
└── tasker/          # Docker Compose setup for Tasker services
```

## Quick Reference
| Task | Workflow | Description |
|---|---|---|
| `SETUP` | `workflows/project-setup.md` | Initialize or re-scaffold project modules |
| `ISSUE` | `workflows/create-issue.md` | Create new tasks based on analysis or user request |
| `WORK` | `workflows/implement-issue.md` | Start working on a specific issue |
| `DOCS` | `workflows/update-documentation.md` | Sync all documentation (Code, MD, Web) |
| `HISTORY`| `workflows/daily-log.md` | Update the daily log (bitácora) in `.history/` |
| `TEST` | `workflows/prueba-el-proyecto.md` | Full black-box evaluation of the project |
| `COMMIT`| `workflows/commit-push.md` | Prepare changes for user approval |
| `FIND` | `workflows/convert-findings-to-issues.md` | Convert test report findings into actionable issues |

## Agent Protocol
For detailed rules on how to interact with Tasker and the project, read **[AGENT_GUIDE.md](./AGENT_GUIDE.md)**.

### Service Menu Rule
- **Always end with a Service Menu**: At the end of every response where a task was completed or a decision is needed, present a table of available workflows.
- **Suggest Next Steps**: Based on the current state, highlight the most logical next workflow in **bold**.
- **Wait for Choice**: Unless it's an emergency, wait for the user to select an option (e.g., "1", "Create Issue") before proceeding.

## Core Files
- **project.md**: Project architecture, constraints, and quality standards.
- **project.json**: Machine-readable project metadata.
- **tasker.constraints.yml**: Architectural, technological, and pattern constraints.

---

## Installation & Setup

### Quick Start
```bash
# 1. Install Tasker package
pip install socialseed-tasker

# 2. Scaffold Tasker into your project (creates .agent/ directory)
tasker install

# 3. Initialize your project interactively (configure project details)
tasker init
```

### Non-Interactive Installation
```bash
tasker install /path/to/project --force \
  --project-name "my-app" \
  --architecture "api-first" \
  --language "python" \
  --framework "fastapi" \
  --database "postgresql" \
  --github-repo "https://github.com/user/repo"
```

| Flag | Description |
|---|---|
| `--force, -f` | Overwrite existing files with latest templates |
| `--inplace, -i` | Initialize in current directory without creating .agent/ subdirectory |
| `--project-name, -pn` | Project name for agent context |
| `--architecture, -a` | Architecture type: monolithic, microservices, serverless, api-first |
| `--language, -lang` | Programming language (e.g., python, go, typescript) |
| `--framework, -fw` | Framework (e.g., fastapi, react, vue) |
| `--database, -db` | Database (e.g., postgresql, mongodb, neo4j) |
| `--github-repo, -gh` | GitHub repository URL |

---

## CLI Commands Reference

### Global Options
All commands support these options:
```bash
--neo4j-uri        # Neo4j connection URI (default: bolt://localhost:7687)
--neo4j-user, -u  # Neo4j username (default: neo4j)
--neo4j-password, -pw  # Neo4j password (required)
--version, -v     # Show version information
--help            # Show help for any command
```

### tasker serve
Start the Tasker API server.
```bash
# Start on default port (8000)
tasker serve

# Start on custom port
tasker serve --port 9000

# Start with auto-reload (development)
tasker serve --reload

# Bind to specific host
tasker serve --host 0.0.0.0 --port 8080
```

| Option | Description |
|---|---|
| `--host, -h` | Host to bind to (default: 0.0.0.0) |
| `--port, -p` | Port to bind to (default: 8000) |
| `--reload, -r` | Enable auto-reload for development |

### tasker restart
Restart Tasker Docker services.
```bash
# Build and restart all Docker containers
tasker restart

# Start without rebuilding
tasker restart --build false

# Force rebuild (--no-cache)
tasker restart --force
```

| Option | Description |
|---|---|
| `--build, -b` | Build images before starting (default: True) |
| `--force, -f` | Force rebuild with --no-cache (default: False) |

---

## Issue Management

### tasker issue create
Create a new issue.
```bash
tasker issue create "Fix login bug" --component backend --priority HIGH
tasker issue create "Add feature" --component api --priority MEDIUM --labels "feature,auth"
```

| Option | Description |
|---|---|
| `title` (positional) | Issue title (required) |
| `--component, -c` | Component ID to assign the issue to |
| `--priority, -p` | Priority: LOW, MEDIUM, HIGH, CRITICAL (default: MEDIUM) |
| `--labels, -l` | Comma-separated labels |
| `--project` | Project name (for multi-project setups) |

### tasker issue list
List issues with optional filters.
```bash
tasker issue list
tasker issue list --status OPEN
tasker issue list --status OPEN --project myproject --component backend
```

| Option | Description |
|---|---|
| `--status, -s` | Filter by status: OPEN, IN_PROGRESS, BLOCKED, CLOSED |
| `--project, -p` | Filter by project name |
| `--component, -c` | Filter by component ID |
| `--all` | Show all issues including closed |
| `--labels, -l` | Filter by labels (comma-separated) |

### tasker issue show
Show detailed information about an issue.
```bash
tasker issue show abc123
tasker issue show abc123 --dependencies
```

| Option | Description |
|---|---|
| `--dependencies` | Show dependency chain |
| `--affects` | Show affected files |

### tasker issue close
Close an issue.
```bash
tasker issue close abc123
tasker issue close abc123 --affects src/auth.py --affects tests/auth_test.py
```

| Option | Description |
|---|---|
| `--affects` | File paths affected by this issue (can be specified multiple times) |

### tasker issue delete
Permanently delete an issue.
```bash
tasker issue delete abc123
```

### tasker issue move
Move an issue to a different component.
```bash
tasker issue move abc123 --to-component new-component-id
```

### tasker issue start
Mark an issue as IN_PROGRESS.
```bash
tasker issue start abc123
```

### tasker issue finish
Mark an issue as CLOSED (after completion).
```bash
tasker issue finish abc123 --resolution "Fixed by updating dependencies"
```

| Option | Description |
|---|---|
| `--resolution, -r` | Resolution summary |

---

## Component Management

### tasker component create
Create a new component.
```bash
tasker component create api-gateway --project myproject --description "API Gateway service"
```

| Option | Description |
|---|---|
| `name` (positional) | Component name (required) |
| `--project, -p` | Project name (required) |
| `--description, -d` | Component description |
| `--labels, -l` | Comma-separated labels |

### tasker component list
List all components.
```bash
tasker component list
tasker component list --project myproject
```

### tasker component show
Show component details.
```bash
tasker component show component-id
```

### tasker component update
Update component properties.
```bash
tasker component update component-id --name new-name --description "Updated description"
```

### tasker component delete
Delete a component and all associated issues.
```bash
tasker component delete component-id
```

### tasker component add-dependency
Add a dependency relationship between components.
```bash
tasker component add-dependency component-a --depends-on component-b
```

### tasker component list-dependencies
List dependencies of a component.
```bash
tasker component list-dependencies component-id
```

---

## Dependency Management

### tasker dependency add
Create a DEPENDS_ON relationship between two issues.
```bash
tasker dependency add abc123 --depends-on xyz789
```

### tasker dependency remove
Remove a dependency relationship.
```bash
tasker dependency remove abc123 xyz789
```

### tasker dependency list
List all issues that the given issue depends on.
```bash
tasker dependency list abc123
```

### tasker dependency chain
Get the full transitive dependency chain for an issue.
```bash
tasker dependency chain abc123
```

### tasker dependency blocked
List all issues blocked by open dependencies.
```bash
tasker dependency blocked
```

---

## Analysis Commands

### tasker analyze impact
Analyze the downstream impact of an issue.
```bash
tasker analyze impact abc123
```

### tasker analyze code-impact
Analyze code-level impact of a file change.
```bash
tasker analyze code-impact src/auth.py
```

### tasker analyze root-cause
Find likely root causes for a test failure or issue.
```bash
tasker analyze root-cause abc123
```

### tasker analyze similarity
Detect phantom dependencies using RAG semantic similarity.
```bash
tasker analyze similarity --issue abc123
tasker analyze similarity --issue abc123 --threshold 0.7 --limit 10
```

| Option | Description |
|---|---|
| `--issue` | Issue ID to analyze (required) |
| `--threshold, -t` | Similarity threshold 0.0-1.0 (default: 0.7) |
| `--limit, -l` | Max number of results (default: 10) |

### tasker analyze architect
Validate architectural constraints for an issue.
```bash
tasker agent architect --issue abc123
tasker agent architect --issue abc123 --check
```

| Option | Description |
|---|---|
| `--issue` | Issue ID to validate (required) |
| `--check` | Run constraint validation check |

---

## Code Graph Commands

### tasker code-graph scan
Scan and index a codebase.
```bash
tasker code-graph scan /path/to/repo
tasker code-graph scan /path/to/repo --language python
```

| Option | Description |
|---|---|
| `path` (positional) | Path to scan (default: current directory) |
| `--language, -lang` | Filter by programming language |
| `--incremental` | Only scan changed files since last scan |

### tasker code-graph find
Find code symbols by name, type, or language.
```bash
# Find by name
tasker code-graph find --name "function_name"

# Find by type
tasker code-graph find --type class --name "UserService"

# Find by language
tasker code-graph find --language python --name "handler"
```

| Option | Description |
|---|---|
| `--name, -n` | Symbol name to search for |
| `--type, -t` | Symbol type: function, class, method, variable |
| `--language, -lang` | Filter by programming language |

### tasker code-graph files
List all indexed code files.
```bash
tasker code-graph files
tasker code-graph files --language python --limit 50
```

### tasker code-graph stats
Show code graph statistics.
```bash
tasker code-graph stats
```

### tasker code-graph impact
Show impact analysis for a symbol.
```bash
tasker code-graph impact symbol-id
```

### tasker code-graph calls
Find all functions that call a specific symbol.
```bash
tasker code-graph calls symbol-id
```

### tasker code-graph depends
Show dependencies of a symbol.
```bash
tasker code-graph depends symbol-id
```

### tasker code-graph tests
Find tests related to a symbol.
```bash
tasker code-graph tests symbol-id
```

### tasker code-graph file
Get detailed information about a file.
```bash
tasker code-graph file src/auth.py
```

### tasker code-graph clear
Clear the code graph database.
```bash
tasker code-graph clear
```

---

## RAG Commands (Semantic Search)

### tasker rag search
Perform semantic search across task history and codebase.
```bash
tasker rag search "how to implement authentication"
tasker rag search "caching strategy" --limit 5
```

| Option | Description |
|---|---|
| `query` (positional) | Natural language search query (required) |
| `--limit, -l` | Max number of results (default: 10) |
| `--source, -s` | Filter by source: issue, code, reasoning |

### tasker rag index
Index content for RAG search.
```bash
tasker rag index --source issue --id abc123
tasker rag index --source all
```

| Option | Description |
|---|---|
| `--source, -s` | Source type: issue, code, reasoning, all |
| `--id` | ID of specific item to index |

### tasker rag stats
Show RAG index statistics.
```bash
tasker rag stats
```

### tasker rag clear
Clear the RAG index.
```bash
tasker rag clear --yes
```

---

## Agent Commands

### tasker agent context
Get agent context for a specific issue (context window for LLMs).
```bash
tasker agent context --issue abc123
tasker agent agent context --issue abc123 --depth 2
```

| Option | Description |
|---|---|
| `--issue` | Issue ID to get context for (required) |
| `--depth, -d` | Dependency analysis depth (default: 2) |

### tasker agent suggest
Get AI suggestions for an issue.
```bash
tasker agent suggest --issue abc123
```

### tasker agent reasoning
View AI reasoning history for an issue.
```bash
tasker agent reasoning --issue abc123
```

### tasker agent register
Register a new agent with Tasker.
```bash
tasker agent register --id agent-001 --name "Developer Agent" \
  --role developer --capabilities "coding,testing,code-review"
```

| Option | Description |
|---|---|
| `--id, -i` | Unique agent identifier (required) |
| `--name, -n` | Human-readable agent name (required) |
| `--role, -r` | Agent role: developer, reviewer, planner, observer (required) |
| `--capabilities, -c` | Comma-separated capabilities (required) |

### tasker agent specialize
Assign an agent to specialize in a component.
```bash
tasker agent specialize --agent agent-001 --component backend
```

| Option | Description |
|---|---|
| `--agent, -a` | Agent ID (required) |
| `--component, -c` | Component ID to specialize in (required) |

### tasker agent list
List all registered agents.
```bash
tasker agent list
```

### tasker agent dispatch
Assign OPEN issues to agents based on priority.
```bash
tasker agent dispatch
tasker agent dispatch --limit 5
```

| Option | Description |
|---|---|
| `--limit, -l` | Max issues to dispatch (default: 5) |

---

## Reasoning Commands

### tasker reasoning log
Log a reasoning entry for an issue.
```bash
tasker reasoning log --issue abc123 \
  --thought "Implementing hexagonal architecture for X" \
  --decision "Hexagonal" \
  --alternatives "Layered, Monolithic" \
  --rejected "Layered is too coupled"
```

| Option | Description |
|---|---|
| `--issue` | Issue ID (required) |
| `--thought` | Reasoning thought process |
| `--decision` | Decision made |
| `--alternatives` | Alternative options considered |
| `--rejected` | Options that were rejected and why |

### tasker reasoning history
View reasoning history for an issue.
```bash
tasker reasoning history --issue abc123
```

### tasker reasoning stats
Show reasoning statistics.
```bash
tasker reasoning stats
```

### tasker reasoning clear
Clear reasoning logs.
```bash
tasker reasoning clear --issue abc123
```

---

## Constraints Commands

### tasker constraints set
Add a new constraint rule.
```bash
tasker constraints set --name "no-circular-deps" \
  --rule "no_circular_dependencies" \
  --level hard \
  --description "Circular dependencies are not allowed"
```

| Option | Description |
|---|---|
| `--name, -n` | Constraint name (required) |
| `--rule, -r` | Rule pattern (required) |
| `--level, -l` | Enforcement level: hard, soft (default: hard) |
| `--description, -d` | Human-readable description |

### tasker constraints list
List all active constraints.
```bash
tasker constraints list
tasker constraints list --category architecture
```

| Option | Description |
|---|---|
| `--category, -c` | Filter by category: architecture, technology, naming, patterns, dependencies |

### tasker constraints validate
Validate current project state against constraints.
```bash
tasker constraints validate
```

---

## Storage Commands

### tasker storage migrate
Run database migrations.
```bash
tasker storage migrate --version 0.9.0
```

### tasker storage rollback
Rollback to a previous version.
```bash
tasker storage rollback --version 0.8.0
```

---

## Project Commands

### tasker project detect
Detect project structure and modules.
```bash
tasker project detect --path /path/to/project
```

### tasker project setup
Setup project structure for Tasker.
```bash
tasker project setup --path /path/to/project
```

---

## Seed Data

### tasker seed run
Populate database with demo data for first-time users.
```bash
tasker seed run
```

---

## Authentication

### tasker login
Save credentials for future sessions.
```bash
tasker login --uri bolt://localhost:7687 --user neo4j --password secret
```

| Option | Description |
|---|---|
| `--uri` | Neo4j connection URI |
| `--user, -u` | Neo4j username |
| `--password, -pw` | Neo4j password |

### tasker logout
Clear saved credentials.
```bash
tasker logout
```

---

## Status

### tasker status
Show CLI status and configuration.
```bash
tasker status
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `TASKER_NEO4J_URI` | Neo4j connection URI | bolt://localhost:7687 |
| `TASKER_NEO4J_USER` | Neo4j username | neo4j |
| `TASKER_NEO4J_PASSWORD` | Neo4j password | (required) |
| `TASKER_API_URL` | Tasker API URL | http://localhost:8000 |
| `OPENAI_API_KEY` | OpenAI API key for RAG features | (optional) |

---

## See Also
- [AGENT_GUIDE.md](./AGENT_GUIDE.md) - Agent interaction protocol
- [project.md](./project.md) - Project architecture and constraints
- [workflows/](./workflows/) - Step-by-step procedural guides
- [skills/](./skills/) - Specialized capabilities documentation