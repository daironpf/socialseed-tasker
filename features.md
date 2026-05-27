# Features - SocialSeed Tasker (v1.0.2)

This document documents all functionalities implemented in versions 1.0.0 through 1.0.2.

## v1.0.2 Improvements

| Area | Change | Details |
|------|--------|---------|
| **Docker** | Build context fix | `docker-compose.yml` template uses `context: ../..` + `dockerfile: .agent/tasker/Dockerfile` so `COPY` from project root resolves correctly |
| **API** | DB connection error → 503 | `GraphPortError` returns `503 DATABASE_CONNECTION_ERROR` instead of generic 500. Also detects `ServiceUnavailable`, `Neo4jError`, `SessionExpired` in generic handler |
| **Repositories** | Import alias fixes | `PolicyRepository`, `UserRepository`, `CommitRepository`, `CodeGraphRepository` — all fixed `NameError` from `import queries as neo4j_queries` + `queries.XXX` usage |
| **CLI** | Windows emoji crash fix | Replaced `🎉` with `SUCCESS:` in `init_command.py` to avoid `UnicodeEncodeError` on cp1252 terminal |

---

## 1. Core Task Management

### 1.1 Neo4j as Exclusive Storage

Only Neo4j is supported as storage backend (file storage removed in v0.5.0).

```bash
# Configure Neo4j connection
export TASKER_NEO4J_URI=bolt://localhost:7687
export TASKER_NEO4J_USER=neo4j
export TASKER_NEO4J_PASSWORD=your-password

# For Neo4j Aura DB (auto-detects encryption from URI)
export TASKER_NEO4J_URI=bolt+s://your-instance.databases.neo4j.io:7687
```

---

### 1.2 Short UUID Support

All commands support partial UUIDs (8+ characters).

```bash
# These are equivalent
tasker issue show 550e8400-e29b-41d4-a716-446655440000
tasker issue show 550e8400
```

---

### 1.3 Component Management

Components organize issues by service/module.

```bash
# Create component via CLI
tasker component create backend -p my-project --description "Backend service"

# Create component via API
curl -X POST http://localhost:8000/api/v1/components \
  -H "Content-Type: application/json" \
  -d '{"name": "backend", "project": "my-project", "description": "Backend service"}'

# List all components
tasker component list

# Get component details
tasker component show <component-id>

# Update component
tasker component update <component-id> --description "Updated description"

# Delete component
tasker component delete <component-id>
```

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique identifier |
| `name` | string | Component name (unique per project) |
| `project` | string | Project name |
| `description` | string | Optional description |
| `created_at` | datetime | Creation timestamp |

---

### 1.4 Issue Management

Issues represent tasks or bugs to be addressed.

```bash
# Create issue via CLI
tasker issue create "Fix login bug" -c backend -p HIGH --description "Users cannot login"

# Create issue via API
curl -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{"title": "Fix login bug", "component_id": "<uuid>", "priority": "HIGH"}'

# List issues (paginated)
tasker issue list --status OPEN --priority HIGH --page 1

# Get issue details
tasker issue show <issue-id>

# Update issue (PATCH)
curl -X PATCH http://localhost:8000/api/v1/issues/<id> \
  -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}'

# Close issue (validates dependencies)
tasker issue close <issue-id>

# Delete issue
tasker issue delete <issue-id>
```

| Status | Description |
|--------|-------------|
| `OPEN` | Issue created, not started |
| `IN_PROGRESS` | Agent working on it |
| `BLOCKED` | Waiting on dependencies |
| `CLOSED` | Completed |

| Priority | Description |
|----------|-------------|
| `LOW` | Lowest priority |
| `MEDIUM` | Normal priority |
| `HIGH` | High priority |
| `CRITICAL` | Urgent priority |

---

### 1.5 Dependency Management

Dependencies track relationships between issues using Neo4j graph edges.

```bash
# Add dependency (Issue A depends on Issue B)
tasker dependency add <issue-a-id> --depends-on <issue-b-id>

# Get dependency chain
tasker dependency chain <issue-id>

# List all dependencies
tasker dependency list

# Get blocked issues
tasker dependency blocked
```

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/issues/{id}/dependencies` | POST | Add dependency |
| `/api/v1/issues/{id}/dependencies` | GET | List dependencies |
| `/api/v1/issues/{id}/dependency-chain` | GET | Full chain with BFS |
| `/api/v1/graph/dependencies` | GET | Full graph visualization |
| `/api/v1/blocked-issues` | GET | Issues blocked by dependencies |

---

## 2. Workable Issues

Issues ready to work on (all dependencies closed).

```bash
# CLI
tasker issue workable

# API
curl http://localhost:8000/api/v1/workable-issues?priority=HIGH
```

---

## 3. Analysis Features

### 3.1 Impact Analysis

Analyze which issues would be affected if an issue fails.

```bash
tasker analyze impact <issue-id>
curl http://localhost:8000/api/v1/analyze/impact/<issue-id>

# Response:
{
  "directly_affected": [...],
  "transitively_affected": [...],
  "blocked_issues": [],
  "risk_level": "CRITICAL|HIGH|MEDIUM|LOW"
}
```

| Risk Level | Criteria |
|------------|----------|
| `CRITICAL` | 5+ transitive dependents |
| `HIGH` | 3-4 transitive dependents |
| `MEDIUM` | 1-2 transitive dependents |
| `LOW` | No dependents |

---

### 3.2 Component Impact Analysis

Analyze component criticality based on its issues.

```bash
curl http://localhost:8000/api/v1/analyze/component-impact/<component-id>

# Response:
{
  "total_issues": 15,
  "directly_affected": [...],
  "transitively_affected": [...],
  "criticality_score": 0.75,
  "risk_level": "MEDIUM"
}
```

---

### 3.3 Root Cause Analysis

Detect likely root causes for test failures.

```bash
curl -X POST http://localhost:8000/api/v1/analyze/root-cause \
  -H "Content-Type: application/json" \
  -d '{"test_failure": "test_login fails", "component_id": "<uuid>"}'

# Scoring based on:
# - Component match
# - Temporal recency
# - Label overlap
# - Semantic similarity
# - Graph proximity
```

---

## 4. Project Dashboard

Aggregate statistics for a project.

```bash
curl http://localhost:8000/api/v1/projects/<project-name>/summary

# Response:
{
  "total_issues": 45,
  "by_status": {"OPEN": 10, "IN_PROGRESS": 5, "BLOCKED": 2, "CLOSED": 28},
  "by_priority": {"LOW": 15, "MEDIUM": 20, "HIGH": 8, "CRITICAL": 2},
  "components_count": 4,
  "blocked_issues_count": 2,
  "workable_issues_count": 8,
  "dependency_health": 0.85,
  "top_blocked_components": [...],
  "critical_path_length": 5
}
```

---

## 5. Security Features

### 5.1 API Authentication

Protect API endpoints with API key.

```bash
export TASKER_API_KEY=your-secret-key
export TASKER_AUTH_ENABLED=true

# Authenticate with Bearer token
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/api/v1/issues
# or with X-API-Key header
curl -H "X-API-Key: your-secret-key" http://localhost:8000/api/v1/issues
```

---

### 5.2 Input Validation

XSS and Neo4j injection prevention.

- HTML tags stripped
- Cypher keywords escaped
- Special characters neutralized

---

### 5.3 Rate Limiting

Configurable per-minute request limits.

```bash
export TASKER_RATE_LIMIT_ENABLED=true
export TASKER_RATE_LIMIT_PER_MINUTE=100

# Returns 429 when limit exceeded
```

---

## 6. GitHub Integration

### 6.1 GitHub Adapter

Map Tasker issues to GitHub issues.

```bash
export GITHUB_TOKEN=ghp_xxxx
export GITHUB_REPO=owner/repo
export GITHUB_WEBHOOK_SECRET=secret
```

---

### 6.2 Webhook Listener

Real-time GitHub updates.

```bash
# GitHub sends POST here
curl -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{...payload...}'

# Test webhook
curl http://localhost:8000/api/v1/webhooks/github/test
```

---

### 6.3 Causal Mirroring

Automatic sync of Tasker Analysis as GitHub Issue comments.

---

### 6.4 Offline-First Sync

Queue system for batch sync during outages.

```bash
curl http://localhost:8000/api/v1/sync/status
curl http://localhost:8000/api/v1/sync/queue
curl -X POST http://localhost:8000/api/v1/sync/force
```

---

### 6.5 Label-to-Graph Mapping

Sync GitHub Labels directly into Neo4j nodes.

---

### 6.6 Webhook Signature Validator

Secure endpoint for real-time bidirectional GitHub sync.

---

### 6.7 GitHub Issue Mapper

Map Tasker UUIDs to GitHub Issue numbers.

---

### 6.8 Markdown Transformer

Convert Graph Analysis to GitHub-flavored Markdown.

---

### 6.9 Secret Manager

Secure GitHub PAT handling via environment injection.

---

## 7. Policy & Constraints

### 7.1 Constraints Configuration System

Define constraints in `tasker.constraints.yml` with enforcement levels.

```yaml
constraints:
  - name: no-mongodb
    description: MongoDB is forbidden
    category: technology
    level: hard  # soft=warning, hard=block
    rule:
      forbidden:
        - mongodb
```

```bash
# API operations
curl http://localhost:8000/api/v1/constraints
curl -X POST http://localhost:8000/api/v1/constraints \
  -d '{"name": "no-mongodb", "category": "technology", "level": "hard", "rule": {...}}'
curl http://localhost:8000/api/v1/constraints/validate/<issue-id>
```

| Level | Behavior |
|-------|----------|
| `soft` | Warning only |
| `hard` | Blocks the operation |

---

### 7.2 Dependency Guard

Prevents circular dependencies at write time.

```bash
# Returns 409 Conflict if circular dependency detected
curl -X POST http://localhost:8000/api/v1/issues/<issue-a>/dependencies \
  -d '{"depends_on_id": "<issue-b-id>"}'
```

---

### 7.3 Graph Policy Engine

Enforces architectural rules at write time.

---

## 8. Agent Lifecycle & Observability

### 8.1 Agent Working Indicator

Track which agent is working on an issue.

```bash
curl -X PATCH http://localhost:8000/api/v1/issues/<id> \
  -H "Content-Type: application/json" \
  -d '{"agent_working": true, "agent_id": "agent-123"}'

# UI shows cyan robot icon for agent_working=true
```

---

### 8.2 AI Reasoning Logs

In-issue Markdown summaries explaining architectural choices.

```markdown
## Agent Reasoning
- Decision: Use Redis for caching
- Alternatives considered: Memcached, local cache
- Confidence: 85%
- Reasoning: Better scaling and cluster support
```

---

### 8.3 Live Agent Documentation

Dynamic progress manifest in issues.

```markdown
## Agent Progress Manifest
### Live TODO
- [ ] Sub-task 1
- [x] Sub-task 2

### Affected Files
- src/core/module.ts

### Technical Debt Notes
- Temporary workaround
- TODO for future refactoring
```

---

### 8.4 Agent Lifecycle Integration

Full tracking of agent_working state with start/finish timestamps.

---

## 9. Data Management

### 9.1 Demo Mode

Load sample data on startup.

```bash
export TASKER_DEMO_MODE=true
```

---

### 9.2 Data Reset

Reset all or specific data.

```bash
curl -X POST http://localhost:8000/api/v1/admin/reset \
  -H "Content-Type: application/json" \
  -d '{"scope": "all"}'
```

---

### 9.3 Seed Data

Load demo data via CLI.

```bash
tasker seed run
```

---

## 10. Project Scaffolding

Inject Tasker infrastructure into external projects (v1.0.2 fixes Windows cp1252 compatibility in init output).

```bash
tasker init .

# Force overwrite
tasker init . --force

# Creates:
# - .tasker/
# - docker-compose.yml
# - .env.example
```

---

## 11. Graph Visualization

### 11.1 Interactive Dependency Graph

Graph visualization data endpoint with vis-network.

```bash
curl http://localhost:8000/api/v1/graph/dependencies?project=my-app

# Response: {"nodes": [...], "edges": [...]}
```

---

### 11.2 Vue.js Kanban Board

Frontend UI with drag & drop, auto-refresh every 10 seconds.

---

## 12. Health & Monitoring

### 12.1 Health Check

Neo4j connectivity status.

```bash
curl http://localhost:8000/health

# Response:
{
  "status": "healthy",
  "version": "1.0.2",
  "neo4j": "connected",
  "neo4j_uri": "bolt://localhost:7687",
  "auth_enabled": false
}
```

---

### 12.2 Performance Monitoring

Response time headers and slow request logging.

```bash
curl -v http://localhost:8000/api/v1/issues 2>&1 | grep X-Response-Time
# Output: X-Response-Time-Ms: 45.23
```

```bash
export TASKER_SLOW_REQUEST_THRESHOLD=0.5
# Slow requests logged as warnings
```

### 12.3 Database Connection Error Handling (v1.0.2)

When Neo4j is unreachable, API returns structured `503 DATABASE_CONNECTION_ERROR` responses instead of generic 500.

```bash
# DB down example
curl http://localhost:8000/health
# Response:
{
  "status": "unhealthy",
  "version": "1.0.2",
  "neo4j": "disconnected",
  "error": "..."
}

# Any API call when DB is down:
curl http://localhost:8000/api/v1/issues
# HTTP 503
# Response:
{
  "detail": {
    "code": "DATABASE_CONNECTION_ERROR",
    "message": "Unable to connect to Neo4j. ..."
  }
}
```

Detected exception types:
| Exception | Description |
|-----------|-------------|
| `GraphPortError` | Custom port-level error (e.g. policy validation) |
| `ServiceUnavailable` | Neo4j driver cannot connect |
| `Neo4jError` | Neo4j-side errors (transient) |
| `SessionExpired` | Connection pool / routing issues |

## 13. Feature Flags & Runtime Configuration (v1.0.1)

### 13.1 FeatureFlagStore
Persistent feature flag registry backed by `StoragePort` under key `flags:registry`.

**Methods:**
| Method | Description |
|--------|-------------|
| `get_flag(name)` | Get flag value, returns `None` if missing |
| `set_flag(name, value)` | Set flag (persisted immediately) |
| `list_flags()` | Return all flags as dict |
| `delete_flag(name)` | Delete flag |

### 13.2 FeatureFlagClient
Read flags with precedence:
1. Environment variable `TASKER_FLAG_<NAME>` (JSON-encoded, uppercase, dashes → underscores)
2. In-memory cache (from `FeatureFlagStore`)
3. Default provided to `get_flag`

### 13.3 RuntimeConfig
`RuntimeConfig` wraps store and client with optional dynamic reload via polling.

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_CONFIG_RELOAD` | `0` | Enable dynamic reload polling |
| `TASKER_CONFIG_POLL_SECONDS` | `5` | Polling interval in seconds |

### 13.4 CLI Commands
```bash
tasker flag-set --name <name> --value '<json>'
tasker flag-get --name <name>
tasker flag-list
tasker flag-delete --name <name>
```

### 13.5 Admin API
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/admin/flags` | List all flags |
| GET | `/api/v1/admin/flags/{name}` | Get flag value |
| POST | `/api/v1/admin/flags` | Set flag (`{"name":"...","value":...}`) |
| DELETE | `/api/v1/admin/flags/{name}` | Delete flag |

All endpoints require `admin` RBAC permission.

---

## 14. Data Retention & GDPR Compliance (v1.0.1)

### 14.1 Policy Engine
`evaluate_policy(record_meta)` determines if a record should be kept (`True`) or is eligible for deletion (`False`).

**Default retention periods:**
| Kind | Default |
|------|---------|
| issue | 3 years |
| comment | 2 years |
| log | 90 days |
| storage | 1 year |

**Override via env vars:** `TASKER_RETENTION_<KIND>` (seconds), `TASKER_RETENTION_<TENANT>_<KIND>` (per-tenant override). Records tagged `legal-hold` are always kept.

### 14.2 RetentionWorker
Scans `issue_repo` and `storage` for records exceeding policy.

**Environment Variables:**
| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_RETENTION_ENABLED` | `1` | Enable retention worker |
| `TASKER_RETENTION_INTERVAL` | `3600` | Worker interval in seconds |
| `TASKER_RETENTION_ARCHIVE` | `0` | Archive before deletion |
| `TASKER_RETENTION_ARCHIVE_PATH` | `/tmp/tasker-archives` | Archive output path |
| `TASKER_RETENTION_DRY_RUN` | `0` | Dry-run mode |

### 14.3 Subject Export/Delete (GDPR)
```bash
# Export all data for a subject
curl -X POST http://localhost:8000/api/v1/privacy/export \
  -H "Authorization: Bearer <token>" \
  -d '{"subject_id": "user1"}'

# Request deletion
curl -X POST http://localhost:8000/api/v1/privacy/delete \
  -H "Authorization: Bearer <token>" \
  -d '{"subject_id": "user1", "dry_run": true}'

# Check task status
curl http://localhost:8000/api/v1/privacy/tasks/{task_id}

# View audit log (admin only)
curl http://localhost:8000/api/v1/privacy/audit \
  -H "Authorization: Bearer <token>"
```

All privacy endpoints require `admin` permission or subject ownership.

---

## 15. Multi-Tenant Support (v1.0.1)

### 15.1 TenantContext
Thread-local tenant context using `contextvars`. Provides `get_current_tenant()` and scoped execution via `tenant_context(tenant_id)`.

### 15.2 TenantStore
CRUD operations for tenants backed by `StoragePort` under key `tenants:registry`.

**CLI Commands:**
```bash
tasker tenant-create --id tenant1 --config '{"plan":"premium"}'
tasker tenant-list
tasker tenant-delete --id tenant1
```

**API Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tenants` | List tenants |
| POST | `/api/v1/tenants` | Create tenant |
| GET | `/api/v1/tenants/{tenant_id}` | Get tenant |
| DELETE | `/api/v1/tenants/{tenant_id}` | Delete tenant |

### 15.3 TenantMiddleware
FastAPI middleware that extracts `X-Tenant-ID` header and sets the tenant context per-request.

### 15.4 NamespacedStorage
Storage wrapper that prefixes all keys with `{tenant_id}:`, providing data isolation per tenant.

---

## 16. Data Export & Backup System (v1.0.1)

### 16.1 Backup Core
Functions: `export_data(storage, file_path)`, `verify_export(file_path)`, `restore_data(storage, file_path)`, `list_exports(backup_dir)`. Supports compressed JSON archives with integrity verification via SHA-256.

### 16.2 CLI Commands
```bash
tasker backup create
tasker backup list
tasker backup restore <timestamp>
```

### 16.3 Docker Compose
Scheduled backups via `compose/tools/backup.yml`:
```bash
docker compose -f compose/tools/backup.yml up -d
```

---

## 17. Distributed Tracing (v1.0.1)

### 17.1 OpenTelemetry Integration
`init_tracing()` configures Jaeger exporter, console exporter (optional), and instruments FastAPI, Celery, and Requests.

### 17.2 Environment Variables
| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_OTEL_SERVICE` | `tasker` | Service name for traces |
| `TASKER_JAEGER_HOST` | `localhost` | Jaeger agent host |
| `TASKER_JAEGER_PORT` | `6831` | Jaeger agent UDP port |
| `TASKER_OTEL_SAMPLING_RATE` | `1.0` | Trace sampling ratio |
| `TASKER_OTEL_CONSOLE` | `0` | Enable console span output |

### 17.3 Docker Compose
```bash
docker compose -f compose/infra/tracing.yml up -d
# Jaeger UI: http://localhost:16686
```

### 17.4 Instrumented Components
- `memory_storage.py` (put, get, delete, list_keys)
- `redis_storage.py` (put, get, delete)
- `events/bus.py` (publish, subscribe)
- `events/delivery.py` (deliver, enqueue, attempt)

---

## 18. Chaos Testing Harness (v1.0.1)

### 18.1 Chaosctl
CLI tool for running deterministic chaos scenarios:
```bash
python tools/chaos/chaosctl.py list
python tools/chaos/chaosctl.py run redis-flap
python tools/chaos/chaosctl.py run api-latency
python tools/chaos/chaosctl.py run worker-cpu-spike
python tools/chaos/chaosctl.py status
```

### 18.2 Scenarios
| Scenario | Description |
|----------|-------------|
| `redis-flap` | Restarts Redis container repeatedly to test reconnection |
| `api-latency` | Injects network latency on API container |
| `worker-cpu-spike` | Spikes CPU on worker container to stress resource limits |

### 18.3 Docker Compose
```bash
docker compose -f compose/tools/chaos.yml up -d --build
```

---

## 13. Code-as-Graph (Tree-Sitter)

Deep code analysis and mapping of repository structures.

### 13.1 Multi-Language Support
Automatic AST parsing for multiple languages using Tree-sitter.

| Language | Support Level | Features |
|----------|---------------|----------|
| **Python** | ADVANCED | Classes, Methods, Functions, Imports, Calls, Parameters |
| **JavaScript** | INTERMEDIATE | Classes, Methods, Functions, Imports, Calls |
| **TypeScript** | INTERMEDIATE | Classes, Methods, Functions, Imports, Calls |
| **Java** | BASIC | Classes, Methods |
| **C++** | BASIC | Classes, Structs, Functions |

### 13.2 Code-as-Graph (v0.9.0)
Advanced static analysis that models the codebase in Neo4j.

**Commands:**
*   `tasker code-graph scan <path>`: Scans a directory and builds the graph.
*   `tasker code-graph stats`: Displays graph statistics (files, symbols, relationships).
*   `tasker code-graph files`: Lists all indexed files.
*   `tasker code-graph find <symbol>`: Finds a specific symbol (class/function) in the graph.
*   `tasker code-graph impact <symbol>`: **[NEW]** Analyzes the impact of changing a symbol by finding all its callers.
*   `tasker code-graph clear`: Wipes the code graph data.

### 13.3 Relationship Mapping
Automatically extracts and resolves:
- `[:CONTAINS]`: Class -> Method/Function
- `[:DEFINES]`: File -> Class/Function
- `[:IMPORTS]`: File -> Module
- `[:CALLS]`: Function -> Function (resolved via symbol mapping)

---

## 14. RAG (Retrieval-Augmented Generation)

Semantic search capability using vector embeddings in Neo4j.

### 14.1 Embedding Service
OpenAI text-embedding-3-small model integration with fallback for testing.

| Feature | Description |
|---------|-------------|
| **OpenAI Embeddings** | Uses `text-embedding-3-small` model (1536 dimensions) |
| **Fallback Mode** | Hash-based embeddings when no API key provided |
| **Secret Filtering** | Removes API keys/tokens before embedding |
| **Chunking Strategies** | By paragraph, by lines, by sentences |

### 14.2 RAG Commands (v0.9.0)

```bash
# Search for similar content
tasker rag search "fix memory leak" --limit 5 --threshold 0.7

# Index content for semantic search
tasker rag index --type issue --id <issue-id> --content "Fixed by..."

# Show RAG index statistics
tasker rag stats

# Clear all embeddings
tasker rag clear --yes
```

### 14.3 RAG API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/rag/index` | POST | Index content for RAG |
| `/api/v1/rag/search` | POST | Semantic similarity search |
| `/api/v1/rag/stats` | GET | Index statistics |
| `/api/v1/rag/{source_type}/{source_id}` | DELETE | Delete embeddings for source |
| `/api/v1/rag` | DELETE | Clear all RAG embeddings |

**Example:**
```bash
# Index an issue
curl -X POST "http://localhost:8000/api/v1/rag/index?source_type=issue&source_id=123&content=Fixed memory leak"

# Search
curl -X POST "http://localhost:8000/api/v1/rag/search?query=async%20memory%20fix&limit=5"
```

### 14.4 Vector Index
Neo4j native vector index for similarity search (requires Neo4j 5.11+ with APOC).

```cypher
CREATE VECTOR INDEX rag_index FOR (e:RAGEmbedding) ON e.embedding
OPTIONS {indexConfig: {`vector.dimensions`: 1536, `vector.similarity_function`: 'cosine'}}
```

**Environment Variable:**
```bash
export OPENAI_API_KEY=sk-...  # Required for real embeddings
```

---

## 15. AI Reasoning Logs (Agent Decision Tracking)

Transparent logging of AI agent reasoning for human review and learning.

### 15.1 Graph Pattern
```cypher
(Agent)-[:THOUGHT {timestamp: datetime()}]->(ReasoningNode)-[:DECIDED]->(Issue)
```

### 15.2 ReasoningNode Schema

| Property | Type | Description |
|----------|------|-------------|
| `id` | UUID | Unique identifier |
| `thought` | String | Agent's reasoning text |
| `confidence` | Float | Confidence score (0.0-1.0) |
| `alternatives_considered` | List[String] | Options evaluated |
| `rejected_reasons` | List[String] | Why alternatives were rejected |
| `decision` | String | Decision made |
| `decision_type` | Enum | Type: solution_selection, architecture_choice, etc. |
| `created_at` | DateTime | When thought occurred |

### 15.3 Decision Types

| Type | Description |
|------|-------------|
| `solution_selection` | Choosing between solution options |
| `architecture_choice` | Architectural decisions |
| `priority_decision` | Priority/ordering decisions |
| `dependency_resolution` | Resolving dependencies |
| `refactoring_choice` | Refactoring approach decisions |
| `code_generation` | Code generation decisions |
| `review_decision` | Code review decisions |

### 15.4 Reasoning Commands (v0.9.0)

```bash
# Log agent reasoning for an issue
tasker reasoning log --issue <id> --thought <text> --decision <choice> --confidence 0.8

# View reasoning history
tasker reasoning history [--issue <id>] [--limit 20]

# Show decision statistics
tasker reasoning stats

# Clear reasoning data
tasker reasoning clear [--issue <id>]
```

### 15.5 Reasoning API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/reasoning/log` | POST | Log agent reasoning |
| `/api/v1/reasoning/issue/{issue_id}` | GET | Get reasoning for issue |
| `/api/v1/reasoning/history` | GET | Global reasoning history |
| `/api/v1/reasoning/{id}/feedback` | POST | Add human feedback |
| `/api/v1/reasoning/{id}/feedback` | GET | Get feedback for reasoning |
| `/api/v1/reasoning/stats` | GET | Decision statistics |
| `/api/v1/reasoning/issue/{issue_id}` | DELETE | Delete issue reasoning |
| `/api/v1/reasoning` | DELETE | Clear all reasoning |

**Example - Log reasoning:**
```bash
curl -X POST "http://localhost:8000/api/v1/reasoning/log?issue_id=issue-123&agent_id=agent-1&agent_name=DevAgent&thought=Using buffer strategy&confidence=0.85&decision=add wrapper&decision_type=solution_selection"
```

### 15.6 Automatic Reasoning Capture

An API middleware interceptor automatically captures agent reasoning from the `X-Agent-Reasoning` HTTP header for all requests modifying issues.

**Example Client Flow:**
```bash
curl -X PATCH "http://localhost:8000/api/v1/issues/<issue-id>" \
  -H "X-Agent-Reasoning: {\"thought\": \"Refactoring cache layer\", \"decision\": \"apply_diff\", \"confidence\": 0.9}" \
  -H "Content-Type: application/json" \
  -d '{"status": "IN_PROGRESS"}'
```

---

## 16. Docker & Deployment

### 16.1 Docker Compose

Start all services (v1.0.2 fixes build context for `tasker init` generated projects).

```bash
docker compose up -d
docker compose ps
docker compose logs -f tasker-api
docker compose down
docker compose down -v
```

| Service | Port | Description |
|---------|------|-------------|
| Neo4j | 7474, 7687 | Graph database |
| API | 8000 | REST API |
| Frontend | 8080 | Kanban UI |

---

### 16.2 API Documentation

| Endpoint | Description |
|----------|-------------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc alternative |
| `/openapi.json` | OpenAPI schema |

---

## 17. CLI Commands Reference

### Components
```bash
tasker component create <name> -p <project>
tasker component list
tasker component show <id>
tasker component update <id>
tasker component delete <id>
```

### Issues
```bash
tasker issue create <title> -c <component> -p <priority>
tasker issue list
tasker issue show <id>
tasker issue close <id>
tasker issue workable
```

### Dependencies
```bash
tasker dependency add <issue> --depends-on <dep>
tasker dependency chain <issue>
tasker dependency blocked
tasker dependency list
```

### Analysis
```bash
tasker analyze root-cause <issue>
tasker analyze impact <issue>
tasker analyze similarity <issue-id>
tasker analyze similarity --issue <issue-id> --threshold 0.7
```

### Agent Integration (v1.0.0)
```bash
tasker agent architect --issue <issue-id>
tasker agent architect --issue <issue-id> --check
```

### Code Graph (v0.9.0)
```bash
tasker code-graph scan <path> [--incremental]
tasker code-graph find <name>
tasker code-graph files
tasker code-graph stats
tasker code-graph clear
```

### RAG (Semantic Search)
```bash
tasker rag search <query> [--limit N] [--threshold N]
tasker rag index --type <source_type> --id <source_id> --content <text>
tasker rag stats
tasker rag clear [--yes]
```

### AI Reasoning (Decision Tracking)
```bash
tasker reasoning log --issue <id> --thought <text> [--decision <choice>] [--confidence N]
tasker reasoning history [--issue <id>] [--limit N]
tasker reasoning stats
tasker reasoning clear [--issue <id>] [--yes]
```

### Feature Flags
```bash
tasker flag-set --name <name> --value <json>
tasker flag-get --name <name>
tasker flag-list
tasker flag-delete --name <name>
```

### Backup
```bash
tasker backup create
tasker backup list
tasker backup restore <timestamp>
```

### Tenants
```bash
tasker tenant-create --id <name> [--config '<json>']
tasker tenant-list
tasker tenant-delete --id <name>
```

### Other
```bash
tasker seed run
tasker init <path>
tasker --version
tasker --help
```

---

## 37. Agent Registration & Specialization (v1.0.0)

### 37.1 Agent Registration

Register AI agents for tracking and domain-driven dispatching.

```bash
# CLI - Register agent
tasker agent register --id "agent-001" --name "DevAgent" --role "developer" --capabilities "coding,testing"

# API - Register agent
curl -X POST "http://localhost:8000/api/v1/agents/register" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "name": "DevAgent",
    "role": "developer",
    "capabilities": ["coding", "testing"]
  }'
```

**Agent Roles:**
| Role | Description |
|------|-------------|
| `developer` | Default coding agent |
| `reviewer` | Code review specialist |
| `planner` | Architecture and planning |
| `observer` | Monitoring and reporting |

### 37.2 Agent Specialization

Assign agents to specific components for domain-driven work dispatching.

```bash
# CLI - Add specialization
tasker agent specialize --agent "agent-001" --component "backend-api"

# API - Add specialization
curl -X POST "http://localhost:8000/api/v1/agents/agent-001/specialists/component-id"

# Get agent's specializations
curl "http://localhost:8000/api/v1/agents/agent-001/specialists"

# Get component's specialists
curl "http://localhost:8000/api/v1/components/component-id/specialists"
```

### 37.3 Project-Agent Assignment

Assign agents to projects for team organization.

```bash
# API - Assign agent to project
curl -X POST "http://localhost:8000/api/v1/projects/project-id/agents/agent-id"

# Get project agents
curl "http://localhost:8000/api/v1/projects/project-id/agents"

# Remove agent from project
curl -X DELETE "http://localhost:8000/api/v1/projects/project-id/agents/agent-id"
```

### 37.4 Agent Repository Pattern

Complete repositories for Agent management in Neo4j:

| Repository | Purpose |
|------------|---------|
| `AgentRepository` | CRUD operations for Agent nodes |
| `UserRepository` | User management with project/component relationships |
| `CommitRepository` | Git commit tracking linked to agents/issues |
| `PolicyRepository` | Governance policies enforcement |

*(v1.0.2 fixed `NameError` import aliases in all four repositories — `queries` alias was imported as `neo4j_queries` but used as `queries`)*

---

## 15. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_NEO4J_URI` | `bolt://localhost:7687` | Neo4j URI |
| `TASKER_NEO4J_USER` | `neo4j` | Neo4j user |
| `TASKER_NEO4J_PASSWORD` | - | Neo4j password (required) |
| `API_PORT` | `8000` | API port |
| `TASKER_API_KEY` | - | API key |
| `TASKER_AUTH_ENABLED` | `false` | Enable auth |
| `TASKER_DEMO_MODE` | `false` | Load demo data |
| `TASKER_RATE_LIMIT_PER_MINUTE` | `100` | Rate limit |
| `TASKER_SLOW_REQUEST_THRESHOLD` | `0.5` | Slow threshold |
| `TASKER_ENABLE_PERF_LOGGING` | `true` | Enable perf logging |
| `GITHUB_TOKEN` | - | GitHub PAT |
| `GITHUB_REPO` | - | `owner/repo` |
| `GITHUB_WEBHOOK_SECRET` | - | Webhook secret |
| `TASKER_METRICS_ENABLED` | `0` | Enable Prometheus exporter |
| `TASKER_METRICS_PORT` | `8000` | Prometheus metrics port |
| `TASKER_LOG_LEVEL` | `INFO` | Log level for structured JSON logging |
| `TASKER_CONFIG_RELOAD` | `0` | Enable feature flag dynamic reload |
| `TASKER_CONFIG_POLL_SECONDS` | `5` | Config polling interval |
| `TASKER_OTEL_SERVICE` | `tasker` | OpenTelemetry service name |
| `TASKER_JAEGER_HOST` | `localhost` | Jaeger agent host |
| `TASKER_JAEGER_PORT` | `6831` | Jaeger agent UDP port |
| `TASKER_OTEL_SAMPLING_RATE` | `1.0` | Trace sampling ratio |
| `TASKER_RETENTION_ENABLED` | `1` | Enable retention worker |
| `TASKER_RETENTION_INTERVAL` | `3600` | Retention worker interval |
| `TASKER_RETENTION_ARCHIVE` | `0` | Archive before deletion |
| `TASKER_RETENTION_ARCHIVE_PATH` | `/tmp/tasker-archives` | Archive output path |

---

## 16. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ENTRY POINTS                              │
├─────────────────────────────────────────────────────────────────┤
│  cli/ (argparse)     │  API / Web (FastAPI)                     │
│  cli/main.py         │  entrypoints/web_api/                    │
└──────────┬──────────┴──────────┬──────────────────────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  • Use cases (create_issue, add_dependency, calculate_impact)  │
│  • Protocol ports (GraphPort, ParserPort, IssueRepository)     │
│  • DTOs & exceptions                                            │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  • Entities (Component, Issue, Dependency)                     │
│  • Actions (Create, Update, Delete, Analyze)                   │
│  • Validation (Input sanitization, XSS prevention)             │
│  • Constraints (Policy enforcement, Dependency guard)           │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                   INFRASTRUCTURE LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  • Neo4jGraphAdapter (GraphPort impl)                          │
│  • TreeSitterParser (ParserPort impl)                          │
│  • Neo4j repositories (Issue, Graph, Policy, etc.)             │
│  • Observability (logging, metrics, Prometheus exporter)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE (Neo4j)                               │
├─────────────────────────────────────────────────────────────────┤
│  Graph Database (Neo4j 5.x)                                     │
│  - Issues, Components, Dependencies as nodes & relationships   │
│  - [:BELONGS_TO], [:DEPENDS_ON], [:AFFECTS]                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 17. Performance Targets

| Endpoint | Target | Notes |
|----------|--------|-------|
| GET /issues | <100ms | Indexed queries |
| GET /issues/{id} | <50ms | Unique constraint |
| POST /analyze/impact | <500ms | BFS with depth limit (3) |
| GET /graph/dependencies | <200ms | Index-based traversal |

---

## 18. GitHub Actions CI (v1.0.0)

Automated CI pipeline that runs on every push and PR to `main`/`master`/`develop`.

### 18.1 Pipeline Jobs

| Job | Description | Python Matrix |
|-----|-------------|---------------|
| **lint** | ruff check, black --check, isort --check-only | 3.10, 3.11, 3.12 |
| **typecheck** | mypy src/ with strict settings | 3.10, 3.11, 3.12 |
| **unit-tests** | pytest with `-k "not integration"` | 3.10, 3.11, 3.12 |
| **integration-tests** | pytest with Neo4j service (conditional) | 3.11 |

### 18.2 Manual Dispatch

```bash
# Trigger via GitHub UI with integration=true to run integration tests
# Or set TASKER_INTEGRATION=1 in workflow env
```

### 18.3 CI Badge

```markdown
![CI](https://github.com/<OWNER>/<REPO>/actions/workflows/ci.yml/badge.svg)
```

---

## 19. Developer Tooling (v1.0.0)

Pre-commit hooks and linter configuration for deterministic code quality enforcement.

### 19.1 Pre-commit Hooks

| Hook | Tool | Auto-fix |
|------|------|----------|
| black | Code formatter | Yes |
| isort | Import sorter | Yes |
| ruff | Linter (--fix) | Yes |
| mypy | Type checker | No |

### 19.2 Configuration Files

- `.pre-commit-config.yaml` — Hook definitions with pinned versions
- `pyproject.toml` — `[tool.black]`, `[tool.isort]`, `[tool.ruff]`, `[tool.mypy]` sections
- `mypy.ini` — Strict settings for source, relaxed for tests

### 19.3 Local Setup

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

---

## 20. Observability (v1.0.0)

Structured JSON logging and Prometheus-compatible metrics for all Tasker components.

### 20.1 Structured Logging

JSON-formatted logs with deterministic fields:

```json
{"timestamp": "2026-05-22T12:00:00Z", "level": "INFO", "logger": "tasker.cli", "message": "cli.invoke", "command": "create-issue", "args": {"id": "test-1", "title": "Test"}}
```

### 20.2 Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `tasker_requests_total` | Counter | component, operation, result |
| `tasker_request_duration_seconds` | Histogram | component, operation |
| `tasker_inprogress_requests` | Gauge | component, operation |

### 20.3 Prometheus Exporter

```bash
export TASKER_METRICS_ENABLED=1
export TASKER_METRICS_PORT=8000
# Metrics available at http://localhost:8000/metrics
```

### 20.4 Instrumented Components

- Neo4j adapter (create_node, get_node, run_cypher, delete_node)
- Parser adapter (parse_file)
- CLI wiring (exporter start, logger injection)
- CLI main (command invocation logs, error logs)

---

## 21. Bidirectional Traceability (v1.0.0)

Link issues to code files when closing for full traceability.

### 21.1 AFFECTS Relationship

```bash
# CLI - Link files when closing issue
tasker issue close <issue-id> --affects src/module.py --affects src/utils.py

# API
curl -X POST "http://localhost:8000/api/v1/issues/<id>/close?affected_files=[src/module.py]"
```

### 21.2 Code Graph Integration

```bash
# Scan repository first
tasker code-graph scan src/

# Query issues affecting a file
curl "http://localhost:8000/api/v1/code-graph/issues/<file-path>"
```

---

## 22. Phantom Dependency Detection (v1.0.0)

RAG-powered semantic similarity to find conceptually related but unlinked issues.

### 22.1 Similarity Analysis

```bash
# CLI
tasker analyze similarity --issue <issue-id>
tasker analyze similarity --issue <issue-id> --threshold 0.7 --limit 10

# API
curl "http://localhost:8000/api/v1/analyze/similarity/<issue-id>?threshold=0.7"
```

### 22.2 Detection Flow
- Uses vector embeddings to find semantically similar issues
- Filters out existing explicit dependencies
- Suggests potential phantom dependencies
- Returns similarity scores for review

---

## 23. ARCHITECT Agent (v1.0.0)

Specialized agent role for architectural constraint enforcement.

### 23.1 Agent Role

```bash
# CLI
tasker agent architect --issue <issue-id>
tasker agent architect --issue <issue-id> --check  # Check only, don't veto

# Validates against loaded constraints
# Returns ARCHITECT APPROVED or VETO
```

### 23.2 Constraint Validation
- Validates proposed changes against architectural constraints
- Checks dependency depth limits
- Enforces technology restrictions
- Can block operations with VETO

---

## 24. Epic & Objective Tracking (v1.0.0)

Group issues into epics and define measurable objectives.

### 24.1 Epic Entity
```bash
# Create epic
curl -X POST http://localhost:8000/api/v1/epics \
  -H "Content-Type: application/json" \
  -d '{"title": "User Authentication", "description": "Complete auth system"}'

# List epics
curl http://localhost:8000/api/v1/epics

# Get epic details
curl http://localhost:8000/api/v1/epics/<id>
```

### 24.2 Objective Entity
```bash
# Create objective
curl -X POST http://localhost:8000/api/v1/objectives \
  -H "Content-Type: application/json" \
  -d '{"title": "Reduce login time", "target": "under 500ms", "epic_id": "<id>"}'

# List objectives
curl http://localhost:8000/api/v1/objectives
```

---

## 25. Label Management (v1.0.0)

Color-coded labels for issue categorization.

```bash
# Create label
curl -X POST http://localhost:8000/api/v1/labels \
  -H "Content-Type: application/json" \
  -d '{"name": "bug", "color": "#ff0000", "description": "Bug reports"}'

# List labels
curl http://localhost:8000/api/v1/labels
```

---

## 26. Component Dependencies (v1.0.0)

Track architectural dependencies between components.

```bash
# Add component dependency
tasker component add-dep <component-id> --depends-on <other-component-id>

# List component dependencies
tasker component deps <component-id>
```

---

## 27. Agent Heartbeat (v1.0.0)

Monitor agent activity and detect stalled agents.

```bash
# Register agent with heartbeat
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{"name": "DevAgent", "role": "developer"}'

# Agent heartbeat endpoint
curl -X POST http://localhost:8000/api/v1/agents/<id>/heartbeat

# Check agent status
curl http://localhost:8000/api/v1/agents/<id>/status
```

---

## 28. Storage CLI (v1.0.0)

Database management and health checks.

```bash
# Show storage info
tasker storage info

# Check database health
tasker storage health

# Show storage statistics
tasker storage stats
```

---

## 29. Self-Healing Architecture (v1.0.0)

Automated integrity verification and file hash validation.

### 26.1 File Integrity Guard
- Stores file hashes in CodeFile nodes
- Verifies integrity on read operations
- Auto-detects modified files
- Triggers re-scan for changed files

### 26.2 Integrity Check
```python
# In code_analysis/integrity.py
from socialseed_tasker.core.code_analysis.integrity import verify_file_integrity

# Verify a file's integrity
is_valid = verify_file_integrity(stored_hash, file_path)
```

---

## 30. Constraints CLI (v1.0.0)

Manage project constraints from command line.

```bash
# Set constraint
tasker constraints set --name no-mongodb --level hard --category technology

# List constraints
tasker constraints list

# Validate issue against constraints
tasker constraints validate <issue-id>

# Find documentation gaps
tasker constraints doc-gaps
```

---

## 31. Project Detection (v1.0.0)

Auto-detect project from current directory.

```bash
# Detect project
tasker project detect

# Setup project
tasker project setup --name myproject --repo https://github.com/owner/repo
```

---

## 32. Webhook Management (v1.0.0)

Configure and test external webhooks.

```bash
# List webhooks
curl http://localhost:8000/api/v1/webhooks

# Create webhook
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/webhook", "events": ["issue.created"]}'

# Test webhook
curl -X POST http://localhost:8000/api/v1/webhooks/<id>/test

# Validate webhook payload
curl http://localhost:8000/api/v1/webhooks/validate
```

---

## 33. Sync Engine (v1.0.0)

Offline-first synchronization queue.

```bash
# Get sync status
curl http://localhost:8000/api/v1/sync/status

# Get sync queue
curl http://localhost:8000/api/v1/sync/queue

# Force sync
curl -X POST http://localhost:8000/api/v1/sync/force
```

---

## 34. Cost Analytics (v1.0.0)

Estimate development effort and cost.

```bash
# Get cost estimation for issue
curl http://localhost:8000/api/v1/cost/estimate/<issue-id>

# Get component cost breakdown
curl http://localhost:8000/api/v1/cost/component/<component-id>

# Get project cost summary
curl http://localhost:8000/api/v1/cost/project/<project-name>

# Get cost trend
curl http://localhost:8000/api/v1/cost/trend
```

---

## 35. Admin Operations (v1.0.0)

System administration and data management.

```bash
# Reset database
curl -X POST http://localhost:8000/api/v1/admin/reset \
  -H "Content-Type: application/json" \
  -d '{"scope": "issues"}'

# Clear all data
curl -X POST http://localhost:8000/api/v1/admin/clear
```

---

## 36. API Endpoints Summary (v1.0.0)

Complete list of REST API endpoints:

### Issues
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/issues` | Create issue |
| GET | `/api/v1/issues` | List issues |
| GET | `/api/v1/issues/{id}` | Get issue |
| PUT | `/api/v1/issues/{id}` | Update issue |
| DELETE | `/api/v1/issues/{id}` | Delete issue |
| POST | `/api/v1/issues/{id}/close` | Close issue |
| POST | `/api/v1/issues/{id}/start` | Start work |
| POST | `/api/v1/issues/{id}/finish` | Finish work |
| POST | `/api/v1/issues/{id}/dependencies` | Add dependency |
| POST | `/api/v1/issues/{id}/affects` | Link to code |

### Components
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/components` | List components |
| POST | `/api/v1/components` | Create component |
| GET | `/api/v1/components/{id}` | Get component |
| PUT | `/api/v1/components/{id}` | Update component |
| DELETE | `/api/v1/components/{id}` | Delete component |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/projects` | List projects |
| POST | `/api/v1/projects` | Create project |
| GET | `/api/v1/projects/{id}` | Get project |
| GET | `/api/v1/projects/{id}/summary` | Project dashboard |

### Labels
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/labels` | List labels |
| POST | `/api/v1/labels` | Create label |

### Dependencies
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dependencies` | List dependencies |
| POST | `/api/v1/dependencies` | Create dependency |
| DELETE | `/api/v1/dependencies/{id}` | Delete dependency |

### Analysis
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze/root-cause` | Root cause analysis |
| POST | `/analyze/issue-impact` | Issue impact |
| POST | `/analyze/component-impact` | Component impact |
| GET | `/analyze/code-impact` | Code impact |
| GET | `/analyze/similarity/{issue_id}` | Similarity analysis |

### Code Graph
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/code-graph/scan` | Scan code |
| GET | `/code-graph/files` | List files |
| GET | `/code-graph/symbols` | List symbols |
| GET | `/code-graph/stats` | Statistics |
| GET | `/code-graph/calls/{symbol}` | Call graph |
| GET | `/code-graph/depends/{file}` | Dependencies |
| GET | `/code-graph/tests/{file}` | Test files |
| GET | `/code-graph/issues/{file}` | Issues affecting file |

### RAG
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rag/index` | Index content |
| POST | `/rag/search` | Semantic search |
| GET | `/rag/stats` | RAG statistics |

### Agents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents` | Register agent |
| GET | `/agents` | List agents |
| POST | `/agents/{id}/start` | Start work |
| POST | `/agents/{id}/finish` | Finish work |
| POST | `/agents/{id}/heartbeat` | Heartbeat |

### Reasoning
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/reasoning/log` | Log reasoning |
| GET | `/reasoning/issue/{issue_id}` | Get reasoning |
| GET | `/reasoning/history` | History |

### Policy
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/policy/rules` | Create rule |
| POST | `/policy/validate` | Validate |
| GET | `/policy/rules` | List rules |

### Epics & Objectives
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/epics` | Create epic |
| GET | `/epics` | List epics |
| POST | `/objectives` | Create objective |
| GET | `/objectives` | List objectives |

### Webhooks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/webhooks` | Create webhook |
| GET | `/webhooks` | List webhooks |
| POST | `/webhooks/{id}/test` | Test webhook |

### Sync
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/sync/status` | Sync status |
| GET | `/sync/queue` | Sync queue |
| POST | `/sync/force` | Force sync |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/admin/reset` | Reset data |
| POST | `/admin/clear` | Clear all |
| GET | `/api/v1/admin/flags` | List feature flags |
| GET | `/api/v1/admin/flags/{name}` | Get feature flag |
| POST | `/api/v1/admin/flags` | Set feature flag |
| DELETE | `/api/v1/admin/flags/{name}` | Delete feature flag |
| GET | `/api/v1/admin/rate/{key}` | Get rate limit state |
| POST | `/api/v1/admin/rate/{key}/reset` | Reset rate limit |

### Tenants
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/tenants` | List tenants |
| POST | `/api/v1/tenants` | Create tenant |
| GET | `/api/v1/tenants/{id}` | Get tenant |
| DELETE | `/api/v1/tenants/{id}` | Delete tenant |

### Privacy / GDPR
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/privacy/export` | Export subject data |
| POST | `/api/v1/privacy/delete` | Delete subject data |
| GET | `/api/v1/privacy/tasks/{id}` | Get privacy task status |
| GET | `/api/v1/privacy/audit` | View audit log (admin) |

### Cost
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/cost/estimate/{issue_id}` | Cost estimate |
| GET | `/cost/component/{id}` | Component cost |
| GET | `/cost/project/{name}` | Project cost |
| GET | `/cost/trend` | Cost trend |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/docs` | API docs |
| GET | `/openapi.json` | OpenAPI schema |

---

Version: 1.0.2