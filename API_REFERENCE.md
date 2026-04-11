# API Reference - SocialSeed Tasker v0.8.0

Complete reference for AI agents to interact with Tasker.

---

## Quick Links

| Category | Document |
|----------|----------|
| Issues & Components | [Core CRUD](#crud) |
| Dependencies | [Dependency Graph](#dependencies) |
| Analysis | [Impact & Root Cause](#analysis) |
| GitHub Integration | [GitHub Sync](#github-sync) |
| Policies | [Constraints](#constraints) |

---

## Base URL

```
http://localhost:8000/api/v1
```

---

## Authentication

### Configuration

```bash
# Enable authentication
TASKER_AUTH_ENABLED=true
TASKER_API_KEY=your-secret-key

# All requests require X-API-Key header
curl -H "X-API-Key: your-secret-key" http://localhost:8000/api/v1/issues
```

### Endpoints Without Auth

- `/health`
- `/docs`
- `/openapi.json`
- `/redoc`

---

## <a name="crud"></a>Components

### Create Component
```bash
curl -X POST http://localhost:8000/api/v1/components \
  -H "Content-Type: application/json" \
  -d '{
    "name": "auth-service",
    "description": "Authentication microservice",
    "project": "social-network"
  }'
```

### List Components
```bash
# All components
curl http://localhost:8000/api/v1/components

# By project
curl "http://localhost:8000/api/v1/components?project=social-network"

# By name (exact match)
curl "http://localhost:8000/api/v1/components?name=auth-service"
```

### Get Component
```bash
curl http://localhost:8000/api/v1/components/<component-id>
```

### Update Component
```bash
curl -X PATCH http://localhost:8000/api/v1/components/<component-id> \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Updated description",
    "labels": ["microservice", "auth"]
  }'
```

### Delete Component
```bash
curl -X DELETE http://localhost:8000/api/v1/components/<component-id>
```

---

## Issues

### Create Issue
```bash
curl -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix login bug",
    "description": "Users cannot login with special characters",
    "priority": "HIGH",
    "component_id": "<uuid>",
    "labels": ["bug", "security"]
  }'
```

**enums**:
- `priority`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `status`: `OPEN`, `IN_PROGRESS`, `BLOCKED`, `CLOSED`

### List Issues (Paginated)
```bash
# Basic list
curl "http://localhost:8000/api/v1/issues"

# Filters
curl "http://localhost:8000/api/v1/issues?status=OPEN&priority=HIGH&project=my-app"

# Pagination
curl "http://localhost:8000/api/v1/issues?page=1&page_size=20"
```

**Response format**:
```json
{
  "data": {
    "items": [...],
    "total": 150,
    "page": 1,
    "page_size": 50
  }
}
```

### Get Workable Issues
```bash
# Issues where all dependencies are closed
curl "http://localhost:8000/api/v1/workable-issues"

# With filters
curl "http://localhost:8000/api/v1/workable-issues?priority=HIGH"
```

### Get Issue
```bash
curl http://localhost:8000/api/v1/issues/<issue-id>
```

### Update Issue (PATCH)
```bash
# Update status
curl -X PATCH http://localhost:8000/api/v1/issues/<id> \
  -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}'

# Update priority
curl -X PATCH http://localhost:8000/api/v1/issues/<id> \
  -H "Content-Type: application/json" \
  -d '{"priority": "CRITICAL"}'

# Mark agent working
curl -X PATCH http://localhost:8000/api/v1/issues/<id> \
  -H "Content-Type: application/json" \
  -d '{"agent_working": true}'

# Update description
curl -X PATCH http://localhost:8000/api/v1/issues/<id> \
  -H "Content-Type: application/json" \
  -d '{"description": "New description"}'

# Add labels
curl -X PATCH http://localhost:8000/api/v1/issues/<id> \
  -H "Content-Type: application/json" \
  -d '{"labels": ["bug", "security"]}'
```

### Close Issue
```bash
# Validates all dependencies are closed
curl -X POST http://localhost:8000/api/v1/issues/<id>/close
```

### Delete Issue
```bash
curl -X DELETE http://localhost:8000/api/v1/issues/<id>
```

---

## <a name="dependencies"></a>Dependencies

### Add Dependency
```bash
# Issue A depends on Issue B
curl -X POST http://localhost:8000/api/v1/issues/<issue-a>/dependencies \
  -H "Content-Type: application/json" \
  -d '{"depends_on_id": "<issue-b-id>"}'
```

### List Dependencies
```bash
curl http://localhost:8000/api/v1/issues/<issue-id>/dependencies
```

### Remove Dependency
```bash
curl -X DELETE http://localhost:8000/api/v1/issues/<issue-a>/dependencies/<issue-b>
```

### Get Dependency Chain
```bash
curl http://localhost:8000/api/v1/issues/<issue-id>/dependency-chain
```

### Get Full Graph
```bash
curl "http://localhost:8000/api/v1/graph/dependencies?project=my-app"

# Response: {"nodes": [...], "edges": [...]}
```

### Get Blocked Issues
```bash
curl http://localhost:8000/api/v1/blocked-issues
```

---

## <a name="analysis"></a>Analysis

### Impact Analysis
```bash
# Analyze issue impact
curl http://localhost:8000/api/v1/analyze/impact/<issue-id>

# Returns:
# {
#   "directly_affected": [...],
#   "transitively_affected": [...],
#   "blocked_issues": [...],
#   "risk_level": "HIGH"
# }
```

### Component Impact
```bash
# Analyze component impact
curl http://localhost:8000/api/v1/analyze/component-impact/<component-id>

# Returns:
# {
#   "total_issues": 15,
#   "directly_affected": [...],
#   "transitively_affected": [...],
#   "criticality_score": 0.75,
#   "risk_level": "MEDIUM"
# }
```

### Root Cause Analysis
```bash
# Find likely root causes for test failures
curl -X POST http://localhost:8000/api/v1/analyze/root-cause \
  -H "Content-Type: application/json" \
  -d '{
    "test_failure": "test_login_special_chars fails",
    "component_id": "<uuid>"
  }'

# Returns list of likely root causes with scores
```

---

## Project Dashboard

### Project Summary
```bash
curl http://localhost:8000/api/v1/projects/<project-name>/summary

# Returns:
# {
#   "total_issues": 45,
#   "by_status": {"OPEN": 10, "IN_PROGRESS": 5, "BLOCKED": 2, "CLOSED": 28},
#   "by_priority": {"LOW": 15, "MEDIUM": 20, "HIGH": 8, "CRITICAL": 2},
#   "components_count": 4,
#   "blocked_issues_count": 2,
#   "workable_issues_count": 8,
#   "dependency_health": 0.85,
#   "top_blocked_components": [...],
#   "critical_path_length": 5
# }
```

---

## <a name="github-sync"></a>GitHub Sync

> Requires: `GITHUB_TOKEN`, `GITHUB_REPO`, `GITHUB_WEBHOOK_SECRET`

### Webhook Endpoint
```bash
# GitHub sends POST here
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=<signature>" \
  -d '{...payload...}'
```

### Test Webhook
```bash
# Verify webhook configuration
curl http://localhost:8000/api/v1/webhooks/github/test
```

### Sync Status
```bash
# Get sync status
curl http://localhost:8000/api/v1/sync/status

# Returns: {"is_online": true, "queue_size": 0, "last_sync": "..."}
```

### Sync Queue
```bash
# View pending sync items
curl http://localhost:8000/api/v1/sync/queue
```

### Force Sync
```bash
# Force sync attempt
curl -X POST http://localhost:8000/api/v1/sync/force
```

---

## <a name="constraints"></a>Constraints

### List Constraints
```bash
curl http://localhost:8000/api/v1/constraints
```

### Create Constraint
```bash
curl -X POST http://localhost:8000/api/v1/constraints \
  -H "Content-Type: application/json" \
  -d '{
    "name": "no-mongodb",
    "description": "MongoDB is forbidden",
    "category": "technology",
    "level": "hard",
    "rule": {"forbidden": ["mongodb"]}'
```

### Validate Against Constraints
```bash
# Check if issue violates constraints
curl http://localhost:8000/api/v1/constraints/validate/<issue-id>
```

---

## Admin

### Reset Data
```bash
# Reset all or specific scope
curl -X POST http://localhost:8000/api/v1/admin/reset \
  -H "Content-Type: application/json" \
  -d '{"scope": "all"}'  # "all", "issues", or "components"
```

---

## Health Check

```bash
curl http://localhost:8000/health

# Returns:
# {
#   "status": "healthy",
#   "version": "0.8.0",
#   "neo4j": "connected",
#   "neo4j_uri": "bolt://localhost:7687",
#   "auth_enabled": false
# }
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TASKER_NEO4J_URI` | Yes | Neo4j connection URI |
| `TASKER_NEO4J_USER` | Yes | Neo4j username |
| `TASKER_NEO4J_PASSWORD` | Yes | Neo4j password |
| `TASKER_API_KEY` | No | API authentication key |
| `TASKER_AUTH_ENABLED` | No | Enable auth (`true`/`false`) |
| `TASKER_RATE_LIMIT` | No | Requests/minute (default: 100) |
| `TASKER_DEMO_MODE` | No | Load demo data (`true`/`false`) |
| `GITHUB_TOKEN` | No | GitHub PAT |
| `GITHUB_REPO` | No | `owner/repo` |
| `GITHUB_WEBHOOK_SECRET` | No | Webhook signing secret |

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized |
| 403 | Forbidden (policy violation) |
| 404 | Not Found |
| 409 | Conflict (duplicate, circular dep) |
| 429 | Rate Limited |
| 500 | Internal Error |

---

## Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Description of error",
    "details": [...]
  }
}
```

---

## CLI Commands (Alternative)

```bash
# Install
pip install socialseed-tasker

# Components
tasker component create <name> -p <project>
tasker component list
tasker component show <id>

# Issues
tasker issue create <title> -c <component> -p <priority>
tasker issue list
tasker issue close <id>

# Dependencies
tasker dependency add <issue> --depends-on <dep>
tasker dependency chain <issue>

# Analysis
tasker analyze impact <issue>

# Constraints
tasker constraints list
tasker constraints validate

# Seed demo
tasker seed run

# Init (scaffold external project)
tasker init <path>
tasker init <path> --force
```