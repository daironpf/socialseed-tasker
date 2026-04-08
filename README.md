# SocialSeed Tasker

## 🔭 Graph-Native Engineering & Autonomous Agent Governance

A specialized framework that leverages **Neo4j** to provide AI agents with infinite architectural context and strict governance.

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Architecture-Hexagonal-green.svg" alt="Hexagonal Architecture">
  <img src="https://img.shields.io/badge/Storage-Neo4j%20Only-orange.svg" alt="Neo4j Only">
  <img src="https://img.shields.io/badge/GraphRAG-Enabled-purple.svg" alt="GraphRAG">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0">
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
# Expected: {"status":"healthy","version":"0.6.0"}
```

### 3. Services Available

| Service | URL | Description |
|---------|-----|-------------|
| **Neo4j Browser** | `http://localhost:7474` | Graph database UI (neo4j/neoSocial) |
| **REST API** | `http://localhost:8000` | For AI agents to manage issues |
| **Frontend** | `http://localhost:8080` | Human UI (Kanban board) |
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
Currently no authentication required. Set `ALLOWED_ORIGINS` env var in production.

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

#### List Issues
```bash
# All issues
curl http://localhost:8000/api/v1/issues

# Filter by status
curl "http://localhost:8000/api/v1/issues?status=OPEN"

# Filter by project
curl "http://localhost:8000/api/v1/issues?project=my-app"

# Filter by component
curl "http://localhost:8000/api/v1/issues?component=<component-id>"
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

> **Note:** Currently, `issue show` and `update` endpoints require the full UUID. Short ID support is planned for v0.6.0.

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

def create_issue_and_work(title, component_id, description=""):
    """Create an issue and start working on it."""
    
    # 1. Create the issue
    response = requests.post(f"{API_BASE}/issues", json={
        "title": title,
        "description": description,
        "component_id": component_id,
        "priority": "MEDIUM"
    })
    issue = response.json()["data"]
    issue_id = issue["id"]
    
    # 2. Mark as agent working (shows on board)
    requests.patch(f"{API_BASE}/{issue_id}", json={"agent_working": True})
    
    # 3. Move to in progress
    requests.patch(f"{API_BASE}/{issue_id}", json={"status": "IN_PROGRESS"})
    
    # 4. Do the work...
    
    # 5. Mark as done
    requests.post(f"{API_BASE}/{issue_id}/close")
    
    # 6. Clear agent working flag
    requests.patch(f"{API_BASE}/{issue_id}", json={"agent_working": False})
    
    return issue_id
```

### Full Example: AI Agent Solving an Issue

```python
import requests

API_BASE = "http://localhost:8000/api/v1"

def solve_issue(issue_id, problem_description):
    """
    AI agent solves an issue, keeping the board updated with progress.
    """
    
    # Step 1: Analyze and plan
    todo_items = [
        "Analyze the problem and identify root cause",
        "Write test to reproduce the issue",
        "Implement the fix",
        "Run tests to verify the solution",
        "Update documentation if needed"
    ]
    
    # Step 2: Start working - update status and add TODO to description
    initial_desc = f"## Problem\n{problem_description}\n\n"
    initial_desc += "## TODO:\n" + "\n".join([f"- [ ] {item}" for item in todo_items])
    initial_desc += f"\n\n## Started at: {datetime.now().isoformat()}"
    
    requests.patch(f"{API_BASE}/issues/{issue_id}", json={
        "description": initial_desc,
        "status": "IN_PROGRESS",
        "agent_working": True
    })
    
    # Step 3: First TODO complete - Analyze
    update_issue_description(issue_id, todo_items[0], "Analyzing root cause...")
    
    # Step 4: Found the issue - update with findings
    update_issue_description(issue_id, todo_items[0], 
        "Root cause: Missing null check in auth handler")
    
    # Step 5: Write test
    update_issue_description(issue_id, todo_items[1], 
        "Test written: test_login_with_special_chars")
    
    # Step 6: Implement fix
    update_issue_description(issue_id, todo_items[2], 
        "Fix implemented: Added null validation")
    
    # Step 7: Tests pass
    update_issue_description(issue_id, todo_items[3], 
        "All 45 tests pass")
    
    # Step 8: Close issue with summary
    solution_summary = """
## Solution Applied
- Added null validation for password field
- Added test case with special characters: !@#$%^&*()
- All existing tests continue to pass

## Files Changed
- src/auth/handlers.py (line 45-47)
- tests/test_auth.py (added test_login_with_special_chars)
"""
    
    requests.post(f"{API_BASE}/issues/{issue_id}/close")
    requests.patch(f"{API_BASE}/issues/{issue_id}", json={
        "description": initial_desc + solution_summary,
        "agent_working": False
    })


def update_issue_description(issue_id, completed_item, next_action):
    """Helper to mark a TODO complete and note next action."""
    
    # Get current description
    issue = requests.get(f"{API_BASE}/issues/{issue_id}").json()["data"]
    desc = issue.get("description", "")
    
    # Mark completed item
    desc = desc.replace(f"- [ ] {completed_item}", f"- [x] {completed_item}")
    
    # Add progress note with timestamp
    timestamp = datetime.now().strftime("%H:%M")
    desc += f"\n[{timestamp}] **Next**: {next_action}"
    
    requests.patch(f"{API_BASE}/issues/{issue_id}", json={
        "description": desc
    })
```

### Why Keep the Board Updated?

| Reason | Description |
|--------|-------------|
| **Transparency** | Humans can see what the AI is doing |
| **Traceability** | Full history of the solution is in the issue |
| **Collaboration** | Other agents or humans can see progress |
| **Debugging** | If something goes wrong, the trail is clear |
| **State Sync** | The Kanban board always reflects reality |


def get_workable_issues():
    """Get issues that can be worked on (not blocked)."""
    all_issues = requests.get(f"{API_BASE}/issues").json()["data"]["items"]
    
    workable = []
    for issue in all_issues:
        if issue["status"] == "CLOSED":
            continue
        
        # Check dependencies - if all dependencies are closed, it's workable
        deps = requests.get(f"{API_BASE}/issues/{issue['id']}/dependencies").json()["data"]
        
        if not deps or all(d["status"] == "CLOSED" for d in deps):
            workable.append(issue)
    
    return workable
```

---

## 📋 Complete Example: Full Workflow

```bash
# 1. Create a component
COMPONENT=$(curl -s -X POST http://localhost:8000/api/v1/components \
  -H "Content-Type: application/json" \
  -d '{"name": "api-service", "project": "myapp"}' | jq -r '.data.id')

echo "Created component: $COMPONENT"

# 2. Create multiple issues
ISSUE1=$(curl -s -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Setup database schema\", \"component_id\": \"$COMPONENT\", \"priority\": \"HIGH\"}" | jq -r '.data.id')

ISSUE2=$(curl -s -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d "{\"title\": \"Create API endpoints\", \"component_id\": \"$COMPONENT\", \"priority\": \"HIGH\"}" | jq -r '.data.id')

# 3. Add dependency: API endpoints depend on database schema
curl -X POST "http://localhost:8000/api/v1/issues/$ISSUE2/dependencies" \
  -H "Content-Type: application/json" \
  -d "{\"depends_on_id\": \"$ISSUE1\"}"

# 4. Mark AI is working on database schema
curl -X PATCH "http://localhost:8000/api/v1/issues/$ISSUE1" \
  -H "Content-Type: application/json" \
  -d '{"agent_working": true, "status": "IN_PROGRESS"}'

# 5. After completing database, close it and work on API
curl -X POST "http://localhost:8000/api/v1/issues/$ISSUE1/close"
curl -X PATCH "http://localhost:8000/api/v1/issues/$ISSUE2" \
  -H "Content-Type: application/json" \
  -d '{"agent_working": true, "status": "IN_PROGRESS"}'

# 6. Check all issues
curl http://localhost:8000/api/v1/issues | jq '.data.items[] | {title, status, agent_working, dependencies}'
```

---

## 🔍 Finding Workable Issues

AI agents can query to find issues that are ready to work on:

```bash
# Get all open issues
curl "http://localhost:8000/api/v1/issues?status=OPEN" | jq '.data.items[] | .title'

# For each, check if dependencies are resolved
curl "http://localhost:8000/api/v1/issues/<id>/dependencies"
```

---

## 🧠 GraphRAG: Infinite Context for AI Agents

The Tasker graph isn't just for tracking issues—it's a **knowledge graph** that provides AI agents with infinite context before proposing solutions.

### How It Works

1. **Dependency Tracking**: Every issue relationship is stored as a directed edge in Neo4j
2. **Impact Analysis**: Before working on an issue, agents can query the full dependency chain to understand downstream effects
3. **Root Cause Discovery**: Closed issues are linked to test failures, enabling automated root cause analysis

### Example: Impact Analysis Before a Fix

```python
# Before refactoring the Auth module, check what would be affected
import requests

issue_id = "<auth-module-issue-id>"
impact = requests.get(f"{API_BASE}/analyze/impact/{issue_id}").json()["data"]

print(f"Directly affected: {len(impact['directly_affected'])} issues")
print(f"Transitively affected: {len(impact['transitively_affected'])} issues")
print(f"Risk level: {impact['risk_level']}")
```

This enables the agent to make **informed decisions** based on the complete architectural context, not just the isolated issue.

---

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `TASKER_NEO4J_USER` | `neo4j` | Neo4j username |
| `TASKER_NEO4J_PASSWORD` | (none) | Neo4j password (required) |
| `API_PORT` | `8000` | API server port |

> **Note:** When using Docker Compose, credentials are set via `NEO4J_PASSWORD` in the compose file. Default is `neo4j/neoSocial`.

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
│ • Dependency BFS Analysis     │
│ • Root Cause Detection        │
└────────────┬─────────────────┘
             ▼
┌──────────────────────────────┐
│      Neo4j Graph DB          │
│ (The Source of Truth)        │
│ • Relationship Tracking       │
│ • Causal Traceability         │
└──────────────────────────────┘
```

---

## 🔗 Related Documentation

- **[CLI Reference](#)** - Command-line interface
- **[API Endpoints](#)** - Detailed API documentation
- **[Development](#)** - Running tests, contributing
