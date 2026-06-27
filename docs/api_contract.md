# Tasker API Contract

REST API endpoints for the Tasker backend. All endpoints require the API server to be running.

**Base URL:** `http://localhost:8888` (configurable via `TASKER_API_URL`)

**Authentication:** Optional Bearer token via `Authorization: Bearer <token>` header (configurable via `TASKER_API_KEY`)

---

## Health & Status

### Health Check

```http
GET /health
```

Check if the API server is running and responsive.

**Response:** `200 OK`
```json
{"status": "ok"}
```

---

## Components

### Create Component

```http
POST /api/v1/components
Content-Type: application/json

{
  "name": "auth-service",
  "description": "Authentication service",
  "project": "backend"
}
```

**Response:** `201 Created`

### List Components

```http
GET /api/v1/components?project=backend
```

**Query Parameters:**
- `project` (string, optional): Filter by project name

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "auth-service",
      "description": "Authentication service",
      "project": "backend",
      "created_at": "2026-05-25T10:30:00Z",
      "updated_at": "2026-05-25T10:30:00Z"
    }
  ]
}
```

### Get Component

```http
GET /api/v1/components/{component_id}
```

**Response:** `200 OK` (same structure as above)

**Error:** `404 Not Found` if component doesn't exist

### Update Component

```http
PATCH /api/v1/components/{component_id}
Content-Type: application/json

{
  "description": "Updated description"
}
```

**Response:** `200 OK` (updated component)

### Delete Component

```http
DELETE /api/v1/components/{component_id}
```

**Response:** `204 No Content`

### Component Dependencies

#### Add Dependency

```http
POST /api/v1/components/{component_id}/dependencies
Content-Type: application/json

{
  "depends_on_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

#### List Dependencies

```http
GET /api/v1/components/{component_id}/dependencies
```

**Response:** `200 OK` (array of components)

#### List Dependents

```http
GET /api/v1/components/{component_id}/dependents
```

---

## Issues

### Create Issue

```http
POST /api/v1/issues
Content-Type: application/json

{
  "title": "Fix login bug",
  "description": "Users unable to login with SSO",
  "component_id": "550e8400-e29b-41d4-a716-446655440000",
  "priority": "HIGH",
  "status": "OPEN"
}
```

**Priority values:** `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`

**Status values:** `OPEN`, `IN_PROGRESS`, `BLOCKED`, `RESOLVED`, `CLOSED`

**Response:** `201 Created`

### List Issues

```http
GET /api/v1/issues?component_id=...&statuses=OPEN,IN_PROGRESS&project=backend
```

**Query Parameters:**
- `component_id` (UUID, optional): Filter by component
- `statuses` (comma-separated, optional): Filter by status(es)
- `project` (string, optional): Filter by project
- `page` (integer, optional): Pagination (default: 1)
- `limit` (integer, optional): Items per page (default: 20)

**Response:** `200 OK` (paginated list)

### Get Issue

```http
GET /api/v1/issues/{issue_id}
```

**Response:** `200 OK`

### Update Issue

```http
PATCH /api/v1/issues/{issue_id}
Content-Type: application/json

{
  "title": "Updated title",
  "priority": "CRITICAL",
  "status": "IN_PROGRESS"
}
```

### Close Issue

```http
POST /api/v1/issues/{issue_id}/close
Content-Type: application/json

{
  "resolution": "implemented",
  "commit_sha": "abc123def456"
}
```

**Resolution values:** `implemented`, `duplicate`, `wontfix`, `external`

**Response:** `200 OK` (updated issue with status CLOSED)

### Delete Issue

```http
DELETE /api/v1/issues/{issue_id}
```

**Response:** `204 No Content`

---

## Issue Dependencies

### Add Dependency

```http
POST /api/v1/issues/{issue_id}/dependencies
Content-Type: application/json

{
  "depends_on_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

Creates a blocking relationship: `issue_id` depends on `depends_on_id`.

**Response:** `201 Created`

### Remove Dependency

```http
DELETE /api/v1/issues/{issue_id}/dependencies/{depends_on_id}
```

**Response:** `204 No Content`

### List Issue Dependencies

```http
GET /api/v1/issues/{issue_id}/dependencies
```

Returns list of issues that `issue_id` depends on.

**Response:** `200 OK` (array of issues)

### List Issue Dependents

```http
GET /api/v1/issues/{issue_id}/dependents
```

Returns list of issues that depend on `issue_id`.

**Response:** `200 OK` (array of issues)

### Get Blocked Issues

```http
GET /api/v1/blocked-issues
```

Returns all issues that are currently blocked (have unresolved dependencies).

**Response:** `200 OK` (array of blocked issues)

### Get Workable Issues

```http
GET /api/v1/workable-issues?priority=HIGH&component=auth-service
```

Returns all issues that are not blocked and can be worked on immediately.

**Query Parameters:**
- `priority` (string, optional): Filter by priority
- `component` (string, optional): Filter by component name

---

## Code-as-Graph

### Scan Codebase

```http
POST /api/v1/code-graph/scan
Content-Type: application/json

{
  "path": "/path/to/project",
  "language": "python"
}
```

**Response:** `202 Accepted` (async operation)
```json
{
  "scan_id": "scan-abc123",
  "status": "running"
}
```

### Find Symbol

```http
GET /api/v1/code/symbols?query=MyClass&language=python
```

**Query Parameters:**
- `query` (string): Symbol name or pattern
- `language` (string, optional): Programming language filter

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "symbol-123",
      "name": "MyClass",
      "file": "src/module.py",
      "line": 42,
      "type": "class"
    }
  ]
}
```

---

## Issues-Symbol Relationships

### Add Symbol Relationship

```http
POST /api/v1/issues/{issue_id}/affects
Content-Type: application/json

{
  "symbol_id": "symbol-123"
}
```

Links an issue to a code symbol (e.g., "this issue affects the MyClass implementation").

**Response:** `201 Created`

### Get Affected Symbols

```http
GET /api/v1/issues/{issue_id}/affects
```

Returns all code symbols affected by this issue.

**Response:** `200 OK` (array of symbols)

### Get Issues Affecting Symbol

```http
GET /api/v1/code/symbols/{symbol_id}/issues
```

Returns all issues that affect a specific code symbol.

**Response:** `200 OK` (array of issues)

---

## Reasoning & Analysis

### Add Reasoning Log

```http
POST /api/v1/issues/{issue_id}/reasoning
Content-Type: application/json

{
  "context": "Analyzed database performance metrics",
  "reasoning": "The N+1 query pattern in UserService is causing 95% of slowdowns",
  "related_nodes": ["symbol-456", "symbol-789"]
}
```

**Response:** `201 Created` (updated issue)

### Get Reasoning Logs

```http
GET /api/v1/issues/{issue_id}/reasoning
```

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": "log-1",
      "context": "Analyzed database performance metrics",
      "reasoning": "The N+1 query pattern...",
      "created_at": "2026-05-25T10:30:00Z"
    }
  ]
}
```

---

## Epics & Objectives

### Create Epic

```http
POST /api/v1/epics
Content-Type: application/json

{
  "title": "Migrate to microservices",
  "description": "Break monolith into independent services"
}
```

### List Epics

```http
GET /api/v1/epics
```

### Get Epic

```http
GET /api/v1/epics/{epic_id}
```

### Update Epic

```http
PATCH /api/v1/epics/{epic_id}
Content-Type: application/json

{"title": "Updated title"}
```

### Link Issue to Epic

```http
POST /api/v1/epics/{epic_id}/issues/{issue_id}
```

Associates an issue with an epic.

### Create Objective

```http
POST /api/v1/objectives
Content-Type: application/json

{
  "title": "30% performance improvement",
  "key_results": ["Reduce p99 latency to 200ms", "Improve cache hit ratio to 85%"]
}
```

### Link Epic to Objective

```http
POST /api/v1/objectives/{objective_id}/epics/{epic_id}
```

Associates an epic with a quarterly objective.

---

## Projects

### List Projects

```http
GET /api/v1/projects
```

Returns all distinct project names in the system.

**Response:** `200 OK`
```json
{
  "data": ["backend", "frontend", "infrastructure"]
}
```

---

## Error Responses

All endpoints may return error responses with appropriate HTTP status codes:

### 400 Bad Request
```json
{
  "detail": "Invalid request body",
  "error_code": "INVALID_ENTITY"
}
```

### 401 Unauthorized
```json
{
  "detail": "Invalid or missing API key",
  "error_code": "AUTHENTICATION_ERROR"
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action",
  "error_code": "AUTHORIZATION_ERROR"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND"
}
```

### 409 Conflict
```json
{
  "detail": "Resource already exists or version conflict",
  "error_code": "CONFLICT_ERROR"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error",
  "error_code": "REMOTE_SERVICE_ERROR"
}
```

---

## Pagination

List endpoints support pagination:

```http
GET /api/v1/issues?page=2&limit=50
```

**Response:**
```json
{
  "data": [...],
  "pagination": {
    "page": 2,
    "limit": 50,
    "total": 250,
    "pages": 5
  }
}
```

---

## Authentication

### Bearer Token

If the API requires authentication, include your API key in the `Authorization` header:

```bash
curl -H "Authorization: Bearer sk-abc123def456" \
     http://localhost:8888/api/v1/issues
```

Or via CLI:

```bash
export TASKER_API_KEY=sk-abc123def456
tasker issue list
```

---

## Rate Limiting

The API may implement rate limiting. Check response headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1621862400
```

---

## Testing the API

### Using cURL

```bash
# Check health
curl http://localhost:8888/health

# List components
curl http://localhost:8888/api/v1/components

# Create issue
curl -X POST http://localhost:8888/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{"title":"Test","priority":"HIGH"}'
```

### Using Python

```python
import requests

base_url = "http://localhost:8888"
headers = {"Authorization": "Bearer sk-your-key"}

# Health check
resp = requests.get(f"{base_url}/health")
print(resp.json())

# List issues
resp = requests.get(f"{base_url}/api/v1/issues", headers=headers)
print(resp.json())
```

### Using CLI

```bash
# All these work with both Direct and API modes
tasker component list
tasker issue create "Title" -c component-id -p HIGH
tasker dependency add issue-1 --depends-on issue-2

# Configure for API mode
export TASKER_MODE=api
export TASKER_API_URL=http://localhost:8888

# Same commands now use the API
tasker component list
```

---

## See Also

- [docs/cli_modes.md](./cli_modes.md) - How to switch between Direct and API modes
- [README.md](../README.md) - Project overview
