# Features - SocialSeed Tasker (v0.9.0)

This document documents all functionalities implemented in version 0.9.0.

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

Inject Tasker infrastructure into external projects.

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
  "version": "0.9.0",
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

---

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

---

## 16. Docker & Deployment

### 13.1 Docker Compose

Start all services.

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

### 13.2 API Documentation

| Endpoint | Description |
|----------|-------------|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc alternative |
| `/openapi.json` | OpenAPI schema |

---

## 14. CLI Commands Reference

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

### Other
```bash
tasker seed run
tasker init <path>
tasker --version
tasker --help
```

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

---

## 16. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ENTRY POINTS                              │
├─────────────────────────────────────────────────────────────────┤
│  CLI (Typer)          │  REST API (FastAPI)                     │
│  tasker --help       │  http://localhost:8000/api/v1            │
└──────────┬──────────┴──────────┬──────────────────────────────┘
            │                      │
            ▼                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      CORE LAYER                                 │
├─────────────────────────────────────────────────────────────────┤
│  • Entities (Component, Issue, Dependency)                     │
│  • Actions (Create, Update, Delete, Analyze)                   │
│  • Validation (Input sanitization, XSS prevention)             │
│  • Constraints (Policy enforcement, Dependency guard)              │
│  • Services (GitHub, Webhook, Sync)                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE LAYER                                │
├─────────────────────────────────────────────────────────────────┤
│  Graph Database (Neo4j)                                         │
│  - Issues, Components, Dependencies as nodes                   │
│  - [:BELONGS_TO], [:DEPENDS_ON] relationships                   │
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

Version: 0.9.0