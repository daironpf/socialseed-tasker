# API Reference - v1.0.0

Complete REST API reference for SocialSeed Tasker.

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "username": "neo4j",
  "password": "neoSocial"
}
```

### Admin Auth Required
Some endpoints require admin authentication via header:
```http
X-Admin-Auth: admin_token
```

## Issues

### Create Issue
```http
POST /issues
{
  "title": "Implement feature X",
  "component_id": "uuid",
  "description": "Feature description",
  "priority": "HIGH",
  "labels": ["feature", "backend"]
}
```

### List Issues
```http
GET /issues?status=OPEN&project=myproject&page=1&limit=20
```

### Get Issue
```http
GET /issues/{issue_id}
```

### Update Issue
```http
PATCH /issues/{issue_id}
{
  "title": "Updated title",
  "status": "IN_PROGRESS"
}
```

### Delete Issue
```http
DELETE /issues/{issue_id}
```

### Close Issue
```http
POST /issues/{issue_id}/close?affected_files=["file.py","other.py"]
```

### Close Issue with Affected Files (v1.0.0)
```http
POST /issues/{issue_id}/close
{
  "affected_files": ["path/to/file.py"]
}
```

## Components

### Create Component
```http
POST /components
{
  "name": "api-gateway",
  "project": "myproject",
  "description": "API Gateway service"
}
```

### List Components
```http
GET /components?project=myproject
```

### Get Component
```http
GET /components/{component_id}
```

### Update Component
```http
PATCH /components/{component_id}
{
  "name": "updated-name"
}
```

### Delete Component
```http
DELETE /components/{component_id}
```

## Dependencies

### Add Dependency
```http
POST /issues/{issue_id}/dependencies
{
  "depends_on_id": "target_issue_id"
}
```

### Add Multiple Dependencies
```http
POST /issues/{issue_id}/dependencies/bulk
{
  "depends_on_ids": ["id1", "id2", "id3"]
}
```

### List Dependencies
```http
GET /issues/{issue_id}/dependencies
```

### List Dependents
```http
GET /issues/{issue_id}/dependents
```

### Dependency Chain
```http
GET /issues/{issue_id}/dependency-chain
```

### Blocked Issues
```http
GET /issues/blocked
```

### Workable Issues
```http
GET /issues/workable
```

## Analysis

### Root Cause Analysis
```http
POST /analyze/root-cause
{
  "issue_id": "uuid"
}
```

### Code Impact Analysis
```http
POST /analyze/code-impact
{
  "file_path": "src/main.py"
}
```

### Component Impact Analysis
```http
GET /analyze/component-impact/{component_id}
```

### Full Dependency Graph
```http
GET /analyze/full-graph
```

### Subgraph
```http
GET /analyze/subgraph?root_id=uuid&depth=3
```

### Phantom Dependencies - Similarity (v1.0.0)
```http
GET /analyze/similarity/{issue_id}?threshold=0.7&limit=10
```

## Code Graph (v0.9.0)

### Scan Repository
```http
POST /code-graph/scan
{
  "repository_path": "/path/to/repo"
}
```

### Find Symbols
```http
GET /code-graph/find?name=function_name&type=function
```

### List Files
```http
GET /code-graph/files?language=python
```

### Graph Stats
```http
GET /code-graph/stats
```

### Clear Graph
```http
DELETE /code-graph/clear
```

### Impact Analysis
```http
GET /code-graph/impact/{symbol_id}
```

### Find Callers
```http
GET /code-graph/calls/{symbol_id}
```

### Find Dependencies
```http
GET /code-graph/depends/{symbol_id}
```

### Find Tests
```http
GET /code-graph/tests/{symbol_id}
```

### Get File Details
```http
GET /code-graph/file?path=src/main.py
```

## RAG (v0.9.0)

### Semantic Search
```http
GET /rag/search?q=how+to+implement+auth&limit=5
```

### Find Similar Issues
```http
GET /rag/similar-issues/{issue_id}?limit=5
```

### Generate Embedding
```http
POST /rag/embed
{
  "text": "Issue description text"
}
```

### Index Content
```http
POST /rag/index
{
  "source_type": "issue",
  "source_id": "uuid",
  "content": "Text to index"
}
```

### RAG Stats
```http
GET /rag/stats
```

### Clear RAG Index
```http
DELETE /rag/clear
```

## Reasoning (v0.9.0)

### Add Reasoning Log
```http
POST /issues/{issue_id}/reasoning
{
  "thought": "Chose solution A because...",
  "confidence": 0.85,
  "alternatives_considered": ["solution_b", "solution_c"],
  "rejected_reasons": ["too_complex", "performance_issues"],
  "decision": "Implemented solution A",
  "decision_type": "solution_selection"
}
```

### Get Reasoning Logs
```http
GET /issues/{issue_id}/reasoning
```

### Reasoning History
```http
GET /reasoning/history?limit=50
```

### Reasoning Stats
```http
GET /reasoning/stats
```

### Clear Reasoning
```http
DELETE /reasoning/clear
```

## Agent (v0.9.0)

### Register Agent
```http
POST /agents
{
  "name": "dev-agent-1",
  "role": "DEVELOPER",
  "capabilities": ["code_generation", "testing"]
}
```

### List Agents
```http
GET /agents
```

### Get Agent
```http
GET /agents/{agent_id}
```

### Agent Heartbeat
```http
POST /agents/{agent_id}/heartbeat
{
  "status": "WORKING"
}
```

### Deregister Agent
```http
DELETE /agents/{agent_id}
```

### Get Agent Context
```http
GET /agents/{agent_id}/context?issue_id=uuid
```

### Get Similar Issues for Agent
```http
GET /agents/{agent_id}/similar-issues?issue_id=uuid
```

## Labels

### List Labels
```http
GET /labels
```

### Sync Labels
```http
POST /labels/sync
```

## Policies

### Validate Policy
```http
POST /policies/validate
{
  "policy_id": "uuid",
  "target_type": "issue",
  "target_id": "uuid"
}
```

### List Policies
```http
GET /policies
```

### Get Policy
```http
GET /policies/{policy_id}
```

### Create Policy
```http
POST /policies
{
  "name": "no-circular-deps",
  "rule": "no_circular_dependencies",
  "level": "HARD"
}
```

### Delete Policy
```http
DELETE /policies/{policy_id}
```

### Dry Run Policy
```http
POST /policies/{policy_id}/dry-run
{
  "target_type": "issue",
  "target_id": "uuid"
}
```

## Projects

**Important**: Tasker supports only **ONE project per instance**. The system is designed as a single-project task manager. All issues, components, agents, and code symbols belong to this single project.

### List Projects
```http
GET /projects
```
Returns a list of project names (strings only). Will always return 0 or 1 project.

### List All Projects with Details
```http
GET /projects/all
```
Returns all projects with complete details. Will always return 0 or 1 project.

### Get Current Project
```http
GET /projects/current
```
Returns the single project in the system. This is the primary endpoint to get project info.

**Response:**
```json
{
  "data": {
    "id": "default-project",
    "name": "My Project",
    "slug": "my-project",
    ...
  }
}
```

### Get Project by ID or Slug
```http
GET /projects/{project_id}
```
Returns the project by its ID or slug.

### Create or Get Project
```http
POST /projects
```
If a project already exists, returns the existing one. If not, creates it. Tasker does not allow multiple projects.

**Response (exists):**
```json
{
  "data": {
    "status": "exists",
    "message": "A project already exists. Tasker supports only one project.",
    "project": {
      "id": "default-project",
      "name": "My Project",
      "slug": "my-project"
    }
  }
}
```

## Deployments

### Receive Deployment
```http
POST /deployments
{
  "commit_sha": "abc123",
  "environment": "production",
  "status": "SUCCESS"
}
```

### List Deployments
```http
GET /deployments?environment=production
```

### Get Deployment by Commit
```http
GET /deployments/by-commit/{commit_sha}
```

## Webhooks

### Get Webhook Logs
```http
GET /webhooks/logs
```

### Test Webhook
```http
POST /webhooks/test
```

## Cost Analysis

### Cost Per Component
```http
GET /analytics/cost/component
```

### Cost Per Epic
```http
GET /analytics/cost/epic
```

### Cost Per Project
```http
GET /analytics/cost/project
```

### Cost Summary
```http
GET /analytics/cost/summary
```

## Tenants (v1.0.1)

### Create Tenant
```http
POST /api/v1/tenants
Authorization: Bearer <token>
Content-Type: application/json

{
  "tenant_id": "tenant1",
  "config": {"plan": "premium"}
}
```

### List Tenants
```http
GET /api/v1/tenants
Authorization: Bearer <token>
```

### Get Tenant
```http
GET /api/v1/tenants/{tenant_id}
Authorization: Bearer <token>
```

### Delete Tenant
```http
DELETE /api/v1/tenants/{tenant_id}
Authorization: Bearer <token>
```

All tenant endpoints require `admin` RBAC permission.

## Feature Flags (v1.0.1)

### List Flags
```http
GET /api/v1/admin/flags
Authorization: Bearer <token>
```

### Get Flag
```http
GET /api/v1/admin/flags/{name}
Authorization: Bearer <token>
```

### Set Flag
```http
POST /api/v1/admin/flags
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "beta_feature",
  "value": true
}
```

### Delete Flag
```http
DELETE /api/v1/admin/flags/{name}
Authorization: Bearer <token>
```

All flag endpoints require `admin` RBAC permission.

## Privacy / GDPR (v1.0.1)

### Export Subject Data
```http
POST /api/v1/privacy/export
Authorization: Bearer <token>
Content-Type: application/json

{
  "subject_id": "user1"
}
```
Returns the path to a tar.gz archive containing all data for the subject.

### Delete Subject Data
```http
POST /api/v1/privacy/delete
Authorization: Bearer <token>
Content-Type: application/json

{
  "subject_id": "user1",
  "dry_run": true
}
```
When `dry_run: true`, returns a list of items that would be deleted without actually deleting. Set `dry_run: false` to perform actual deletion.

### Get Privacy Task Status
```http
GET /api/v1/privacy/tasks/{task_id}
Authorization: Bearer <token>
```

### View Audit Log
```http
GET /api/v1/privacy/audit
Authorization: Bearer <token>
```
Requires `admin` permission. Returns the full audit log of all deletion actions.

## System

### Reset Data
```http
POST /system/reset
```

### Get Sync Status
```http
GET /system/sync-status
```

### Get Sync Queue
```http
GET /system/sync-queue
```

### Force Sync
```http
POST /system/force-sync
```

## Epics (v0.9.0)

### Create Epic
```http
POST /epics
{
  "title": "Epic Title",
  "description": "Epic description"
}
```

### List Epics
```http
GET /epics
```

### Get Epic
```http
GET /epics/{epic_id}
```

### Delete Epic
```http
DELETE /epics/{epic_id}
```

### Update Epic
```http
PATCH /epics/{epic_id}
{
  "title": "Updated title"
}
```

### Link Issues to Epic
```http
POST /epics/{epic_id}/issues
{
  "issue_ids": ["uuid1", "uuid2"]
}
```

## Objectives (v0.9.0)

### Create Objective
```http
POST /objectives
{
  "title": "Objective Title",
  "epic_id": "epic_uuid"
}
```

### List Objectives
```http
GET /objectives?epic_id=epic_uuid
```

### Get Objective
```http
GET /objectives/{objective_id}
```

### Delete Objective
```http
DELETE /objectives/{objective_id}
```

### Update Objective
```http
PATCH /objectives/{objective_id}
{
  "status": "COMPLETED"
}
```