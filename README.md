# SocialSeed Tasker

## 🔭 Graph-Native Engineering & Autonomous Agent Governance

A specialized framework that leverages **Neo4j** to provide AI agents with infinite architectural context and strict governance.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Architecture-Hexagonal-green.svg" alt="Hexagonal Architecture">
  <img src="https://img.shields.io/badge/Storage-Neo4j%20Only-orange.svg" alt="Neo4j Only">
  <img src="https://img.shields.io/badge/GraphRAG-Enabled-purple.svg" alt="GraphRAG">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0">
  <img src="https://img.shields.io/badge/Version-0.8.0-green.svg" alt="Version: 0.8.0">
  <img src="https://img.shields.io/badge/PRs-Welcome-green.svg" alt="PRs Welcome">
</p>

---

## 🚀 Quick Start

### 1. Start the Services

```bash
# Clone and start everything with Docker Compose
git clone https://github.com/daironpf/socialseed-tasker.git
cd socialseed-tasker
docker compose up -d
```

### 2. Verify Everything Is Running

```bash
# Check API health
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"0.8.0","neo4j":"connected"}
```

### 3. Services Available

| Service | URL | Description |
|--------|-----|-------------|
| **Neo4j Browser** | `http://localhost:7474` | Graph database UI (neo4j/neoSocial) |
| **REST API** | `http://localhost:8000` | For AI agents to manage issues |
| **Frontend** | `http://localhost:8080` | Human UI (Kanban board & Interactive Graph View) |
| **API Docs** | `http://localhost:8000/docs` | OpenAPI documentation |

### 4. Try It Now - 30-Second Demo

```bash
# Create a component
COMP_ID=$(curl -s -X POST http://localhost:8000/api/v1/components \
  -H "Content-Type: application/json" \
  -d '{"name":"backend","project":"my-app"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Create an issue in that component
ISSUE_ID=$(curl -s -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Fix login bug\",\"component_id\":\"$COMP_ID\",\"priority\":\"HIGH\"}" \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Create a second issue
DEP_ID=$(curl -s -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Add unit tests\",\"component_id\":\"$COMP_ID\",\"priority\":\"MEDIUM\"}" \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Link them: Fix login bug depends on Add unit tests
curl -s -X POST "http://localhost:8000/api/v1/issues/$ISSUE_ID/dependencies" \
  -H "Content-Type: application/json" \
  -d "{\"depends_on_id\":\"$DEP_ID\"}"

# See the dependency chain
curl -s "http://localhost:8000/api/v1/issues/$ISSUE_ID/dependency-chain" | python -m json.tool

# Try to close the issue (will fail - dependency is still open)
curl -s -X POST "http://localhost:8000/api/v1/issues/$ISSUE_ID/close" | python -m json.tool
```

### 5. Or Load Full Demo Data

```bash
# Via CLI (requires local install)
pip install socialseed-tasker
tasker seed run

# Via API env var (auto-seeds on restart)
TASKER_DEMO_MODE=true docker compose restart tasker-api
```

### 6. Explore the Graph

Open **http://localhost:7474** in your browser and run this Cypher query to visualize your data:

```cypher
MATCH (i:Issue)-[:BELONGS_TO]->(c:Component)
RETURN i, c
```

---

## 🔌 REST API Reference for AI Agents

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication

Set `TASKER_API_KEY` and `TASKER_AUTH_ENABLED=true` for production authentication. Health and docs endpoints remain open.

Supports two header formats:
- `X-API-Key: your-key` (original)
- `Authorization: Bearer your-key` (standard)

---

### Components

Components represent different parts of your project (services, modules, packages).

#### Create Component
```bash
curl -X POST http://localhost:8000/api/v1/components \
  -H "Content-Type: application/json" \
  -d '{
    "name": "auth-service",
    "description": "Authentication microservice",
    "project": "social-network"
  }'
```

#### List Components
```bash
curl http://localhost:8000/api/v1/components

# Filter by project
curl "http://localhost:8000/api/v1/components?project=social-network"
```

---

### Issues

#### Create Issue
```bash
# First, get a component ID from the list above
COMPONENT_ID=$(curl -s http://localhost:8000/api/v1/components | python -c "import sys,json; print(json.load(sys.stdin)['data'][0]['id'])")

# Then create an issue
curl -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix login bug with special characters",
    "description": "Users cannot login when password contains special chars",
    "priority": "HIGH",
    "component_id": "'"$COMPONENT_ID"'",
    "labels": ["bug", "security"]
  }'
```

**Priority values**: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

#### List Issues (Paginated)
```bash
# All issues (paginated)
curl "http://localhost:8000/api/v1/issues"

# Response format: {"data": {"items": [...], "total": N, "page": 1, "page_size": 50}}
curl "http://localhost:8000/api/v1/issues?page=1&page_size=20"

# Filter by status
curl "http://localhost:8000/api/v1/issues?status=OPEN"

# Filter by project
curl "http://localhost:8000/api/v1/issues?project=my-app"

# Filter by component
curl "http://localhost:8000/api/v1/issues?component=<component-id>"

# Filter by priority
curl "http://localhost:8000/api/v1/issues?priority=HIGH"
```

#### Get Workable Issues
```bash
# Get issues where all dependencies are closed (ready to work on)
curl "http://localhost:8000/api/v1/workable-issues"

# With filters
curl "http://localhost:8000/api/v1/workable-issues?priority=HIGH&component=<component-id>"
```

#### Update Issue
```bash
# Update status
curl -X PATCH http://localhost:8000/api/v1/issues/<issue-id> \
  -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}'

# Mark that an AI agent is working on this issue
curl -X PATCH http://localhost:8000/api/v1/issues/<issue-id> \
  -H "Content-Type: application/json" \
  -d '{"agent_working": true}'

# Update priority
curl -X PATCH http://localhost:8000/api/v1/issues/<issue-id> \
  -H "Content-Type: application/json" \
  -d '{"priority": "CRITICAL"}'

# Update description
curl -X PATCH http://localhost:8000/api/v1/issues/<issue-id> \
  -H "Content-Type: application/json" \
  -d '{"description": "Updated description"}'

# Close an issue
curl -X POST http://localhost:8000/api/v1/issues/<issue-id>/close
```

**Status values**: `OPEN`, `IN_PROGRESS`, `BLOCKED`, `CLOSED`

#### Delete Issue
```bash
curl -X DELETE http://localhost:8000/api/v1/issues/<issue-id>
```

---

### Dependencies

Dependencies define which issues block others. AI agents use this to understand what can be worked on.

#### Add Dependency
```bash
# Issue A depends on Issue B (B must be completed first)
curl -X POST http://localhost:8000/api/v1/issues/<issue-a-id>/dependencies \
  -H "Content-Type: application/json" \
  -d '{"depends_on_id": "<issue-b-id>"}'
```

#### List Dependencies
```bash
# What does this issue depend on?
curl http://localhost:8000/api/v1/issues/<issue-id>/dependencies
```

#### Remove Dependency
```bash
curl -X DELETE http://localhost:8000/api/v1/issues/<issue-a-id>/dependencies/<issue-b-id>
```

#### Get Dependency Graph
```bash
# Get full dependency graph for a project
curl "http://localhost:8000/api/v1/graph/dependencies?project=my-app"

# Response: {"nodes": [...], "edges": [...]}
```

---

### Agent Working Indicator

AI agents can set `agent_working: true` on an issue to signal they're actively working on it. This displays a cyan robot icon on the Kanban board.

```python
import requests

# Tell the system you're working on this issue
requests.patch(
    "http://localhost:8000/api/v1/issues/<issue-id>",
    json={"agent_working": True}
)

# When done, clear the flag
requests.patch(
    "http://localhost:8000/api/v1/issues/<issue-id>",
    json={"agent_working": False}
)
```

---

### Analysis Endpoints

#### Impact Analysis
```bash
# Analyze what would be affected by an issue
curl "http://localhost:8000/api/v1/analyze/impact/<issue-id>"
# Returns: directly_affected, transitively_affected, blocked_issues, risk_level
```

#### Component Impact
```bash
# Analyze impact for a component
curl "http://localhost:8000/api/v1/analyze/component-impact/<component-id>"
# Returns: total_issues, affected_components, criticality_score, risk_level
```

---

### Project Dashboard

#### Project Summary
```bash
# Get complete project summary
curl "http://localhost:8000/api/v1/projects/<project-name>/summary"
# Returns: total_issues, by_status, by_priority, components_count, blocked_issues_count,
#          workable_issues_count, dependency_health, top_blocked_components, critical_path_length
```

---

### Admin Endpoints

#### Reset Data
```bash
# Reset all data or specific scope
curl -X POST "http://localhost:8000/api/v1/admin/reset" \
  -H "Content-Type: application/json" \
  -d '{"scope": "all"}'  # "all", "issues", or "components"
```

#### Health Check
```bash
# Detailed health with Neo4j connection status
curl http://localhost:8000/health
# Returns: status, version, neo4j (connected/disconnected), neo4j_uri, auth_enabled
```

---

### Sync Service Endpoints

```bash
# Check sync status
curl http://localhost:8000/api/v1/sync/status

# Get sync queue
curl http://localhost:8000/api/v1/sync/queue

# Force sync
curl -X POST http://localhost:8000/api/v1/sync/force
```

---

## 🤖 AI Agent Workflow

### Recommended Workflow for AI Agents

```python
import requests
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def start_working_on_issue(issue_id, todo_items):
    """AI agent starts working on an issue - updates status and sets todo."""
    
    # 1. Create a detailed TODO list in the description
    todo_text = "## TODO:\n" + "\n".join([f"- [ ] {item}" for item in todo_items])
    todo_text += f"\n\n## Progress (started {datetime.now().strftime('%Y-%m-%d %H:%M')}):\n"
    
    requests.patch(f"{API_BASE}/issues/{issue_id}", json={
        "description": todo_text,
        "agent_working": True,
        "status": "IN_PROGRESS"
    })

def update_progress(issue_id, completed_item, next_step):
    """Update progress on the issue."""
    
    # Get current description
    issue = requests.get(f"{API_BASE}/issues/{issue_id}").json()["data"]
    desc = issue.get("description", "")
    
    # Mark completed item
    desc = desc.replace(f"- [ ] {completed_item}", f"- [x] {completed_item}")
    
    # Add progress note
    desc += f"\n- **In progress**: {next_step}"
    
    requests.patch(f"{API_BASE}/issues/{issue_id}", json={
        "description": desc
    })

def finish_issue(issue_id, solution_summary):
    """Mark issue as completed with solution summary."""
    
    # Get current description
    issue = requests.get(f"{API_BASE}/issues/{issue_id}").json()["data"]
    desc = issue.get("description", "")
    
    # Add solution summary
    desc += f"\n\n## Solution:\n{solution_summary}"
    
    # Close the issue
    requests.post(f"{API_BASE}/issues/{issue_id}/close")
    
    # Clear agent working flag
    requests.patch(f"{API_BASE}/issues/{issue_id}", json={
        "description": desc,
        "agent_working": False
    })
```

### Full Example: AI Agent Solving an Issue

```python
import requests
from datetime import datetime

API_BASE = "http://localhost:8000/api/v1"

def solve_issue(issue_id, problem_description):
    """AI agent solves an issue, keeping the board updated with progress."""
    
    todo_items = [
        "Analyze the problem and identify root cause",
        "Write test to reproduce the issue",
        "Implement the fix",
        "Run tests to verify the solution",
        "Update documentation if needed"
    ]
    
    initial_desc = f"## Problem\n{problem_description}\n\n"
    initial_desc += "## TODO:\n" + "\n".join([f"- [ ] {item}" for item in todo_items])
    initial_desc += f"\n\n## Started at: {datetime.now().isoformat()}"
    
    requests.patch(f"{API_BASE}/issues/{issue_id}", json={
        "description": initial_desc,
        "status": "IN_PROGRESS",
        "agent_working": True
    })
    
    # Do work and update progress...
    # Close with summary
    solution_summary = """
## Solution Applied
- Added null validation for password field
- Added test case with special characters
- All existing tests continue to pass
"""
    requests.post(f"{API_BASE}/issues/{issue_id}/close")
    requests.patch(f"{API_BASE}/issues/{issue_id}", json={
        "description": initial_desc + solution_summary,
        "agent_working": False
    })
```

### Finding Workable Issues

```python
def get_workable_issues():
    """Get issues that can be worked on (not blocked)."""
    response = requests.get(f"{API_BASE}/workable-issues")
    return response.json()["data"]["items"]
```

---

## 📦 Project Scaffolding

Inject Tasker infrastructure into any project with a single command. Creates `tasker/` directory with skills, Docker compose, and a full working frontend.

```bash
# Scaffold in current directory
tasker init .

# With overwrite
tasker init . --force

# Initialize without subdirectory
tasker init . --inplace
```

The scaffolded `tasker/` directory includes:
- **Frontend** - Full compiled Vue Kanban board (included in package)
- **API** - Ready to run with Docker Compose
- **Skills** - AI agent skills for task management
- **Configs** - Environment templates

```bash
cd tasker
cp configs/.env.example configs/.env
# Edit configs/.env with your settings
docker compose up -d
```

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `TASKER_NEO4J_USER` | `neo4j` | Neo4j username |
| `TASKER_NEO4J_PASSWORD` | (none) | Neo4j password (required) |
| `API_PORT` | `8000` | API server port |
| `TASKER_API_KEY` | (none) | API key for authentication |
| `TASKER_AUTH_ENABLED` | `false` | Enable API authentication |
| `TASKER_DEMO_MODE` | `false` | Load demo data on startup |
| `TASKER_RATE_LIMIT` | `100` | Requests per minute limit |

---

## 🐳 Docker Compose

The included `docker-compose.yml` starts:
- **Neo4j** (port 7474/7687) - Graph database
- **API** (port 8000) - REST API for AI agents
- **Frontend** (port 8080) - Human Kanban board

```bash
# Start everything
docker compose up -d

# View logs
docker compose logs -f

# Stop everything (data persists in Docker volume)
docker compose down

# Stop and remove all data
docker compose down -v
```

> **Data Persistence**: All data is stored in Neo4j and persists between `docker compose down` and `docker compose up` cycles. Use `docker compose down -v` to completely reset the database.

---

## 📊 Architecture

```
┌──────────────────────────┐
│   AI Agent / Human UI    │
│   REST API (port 8000)   │
└────────────┬─────────────┘
             ▼
┌──────────────────────────────┐
│      Application Core        │
│  (Hexagonal Architecture)    │
│ • Governance Engine           │
│ • Dependency BFS Analysis │
│ • Root Cause Detection     │
│ • Input Validation        │
│ • Rate Limiting          │
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│      Neo4j Graph DB        │
│ (The Source of Truth)         │
│ • Relationship Tracking    │
│ • Causal Traceability    │
└──────────────────────────────┘
```

---

## 🔗 Related Documentation

- **[CLI Reference](#)** - Command-line interface
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API endpoint reference for AI agents
- **[VERSIONS.md](VERSIONS.md)** - Release milestones and feature checklists
- **[Development](#)** - Running tests, contributing