# SocialSeed Tasker

**A graph-based task management framework designed for AI agents to manage issues with infinite context and architectural governance.**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Architecture-Hexagonal-green.svg" alt="Hexagonal Architecture">
  <img src="https://img.shields.io/badge/Storage-File%20or%20Neo4j-orange.svg" alt="File or Neo4j">
</p>

---

## 🚀 Quick Start for AI Agents

### Starting the Server

```bash
# Using Docker Compose (recommended - starts API and frontend)
docker compose up -d

# Or start only the API directly
pip install socialseed-tasker
uvicorn socialseed_tasker.entrypoints.web_api.api:app --host 0.0.0.0 --port 8000
```

### Services Available

| Service | URL | Description |
|---------|-----|-------------|
| **REST API** | `http://localhost:8000` | For AI agents to manage issues |
| **Frontend** | `http://localhost:8080` | Human UI (Kanban board) |
| **API Docs** | `http://localhost:8000/docs` | OpenAPI documentation |

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
```

---

### Issues

#### Create Issue
```bash
curl -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix login bug with special characters",
    "description": "Users cannot login when password contains special chars",
    "priority": "HIGH",
    "component_id": "<component-uuid>",
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

API_BASE = "http://localhost:8000/api/v1"

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

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_STORAGE_BACKEND` | `file` | Storage: `file` or `neo4j` |
| `TASKER_FILE_PATH` | `.tasker-data` | Path for file storage |
| `TASKER_NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection |
| `TASKER_NEO4J_USER` | `neo4j` | Neo4j username |
| `TASKER_NEO4J_PASSWORD` | `` | Neo4j password |
| `API_PORT` | `8000` | API server port |

---

## 🐳 Docker Compose

The included `docker-compose.yml` starts:
- **API** (port 8000) - REST API for AI agents
- **Frontend** (port 8080) - Human Kanban board

```bash
# Start everything
docker compose up -d

# View logs
docker compose logs -f

# Stop everything
docker compose down
```

---

## 📊 Architecture

```
┌─────────────────────────┐
│   AI Agent / CLI        │
│   REST API (port 8000)  │
└───────────┬─────────────┘
            ▼
┌───────────────────────────────┐
│      Application Core          │
│  • Issue Management            │
│  • Dependency Graph           │
│  • Agent Working Tracking     │
└───────────────┬───────────────┘
                ▼
┌─────────────────────┐  ┌─────────────────────┐
│   File Storage      │  │   Neo4j (optional)  │
│   (default)         │  │   Graph queries     │
│   Simple JSON       │  │   Advanced features │
└─────────────────────┘  └─────────────────────┘
```

---

## 💾 Storage Backends

| Backend | Command | Use Case |
|---------|---------|----------|
| **File** (default) | `TASKER_STORAGE_BACKEND=file` | Development, simple setup |
| **Neo4j** | `TASKER_STORAGE_BACKEND=neo4j` | Production, complex graphs |

For file-based storage, data persists in the Docker volume `tasker-data`.

---

## 🔗 Related Documentation

- **[CLI Reference](#)** - Command-line interface
- **[API Endpoints](#]** - Detailed API documentation
- **[Development](#)** - Running tests, contributing