# SocialSeed Tasker

## Graph-Native Engineering & Autonomous Agent Governance

A specialized framework that leverages **Neo4j** to provide AI agents with infinite architectural context and strict governance.

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                        TASKER ARCHITECTURE                         │
├─────────────────────────────────────────────────────────────────────────────┬────────────┤
│                                                               │            │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌───────┐  │   AI     │
│   │  CLI    │────▶│  REST  │────▶│ Action  │────▶│ Repo  │  │   AGENTS │
│   │ (Typer) │     │  API   │     │ Layer  │     │(Neo4j)│  │            │
│   └─────────┘     └─────────┘     └─────────┘     └───────┘  │            │
│        │            │            │            │                 │   Skills  │
│        │            │            │            ▼                 │  (Python)│
│        │            │            │     ┌─────────┐           │            │
│        │            │            │     │ Graph  │           │            │
│        │            │            │     │ DB     │           │            │
│        │            │            │     └─────────┘           │            │
└─────────────────────────────────────────────────────────────────────────────┴────────────┘
```

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Architecture-Hexagonal-green.svg" alt="Hexagonal Architecture">
  <img src="https://img.shields.io/badge/Storage-Neo4j%20Only-orange.svg" alt="Neo4j Only">
  <img src="https://img.shields.io/badge/GraphRAG-Enabled-purple.svg" alt="GraphRAG">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License: Apache 2.0">
  <img src="https://img.shields.io/badge/Version-0.8.1-green.svg" alt="Version: 0.8.1">
  <img src="https://img.shields.io/badge/PRs-Welcome-green.svg" alt="PRs Welcome">
</p>

---

## What's New in v0.8.1

### Performance & Monitoring
- **Response Time Headers**: `X-Response-Time-Ms` on all API responses
- **Slow Request Logging**: Configurable threshold for performance monitoring
- **Optimized Neo4j Indexes**: Faster queries for status, project, and dependency lookups
- **BFS Optimization**: Limited depth traversal for impact analysis

### Security & Dependencies
- **Security Policy**: Comprehensive `SECURITY.md` documenting all security measures
- **Automated Updates**: GitHub Actions workflow for weekly dependency updates
- **pip-audit Integration**: Vulnerability scanning in CI/CD

### Documentation
- **Enhanced API Docs**: Better OpenAPI tags, endpoint descriptions, and examples
- **Performance Targets**: Documented latency goals for all endpoints

---

## Installation

### Prerequisites

- Python 3.10 or higher
- Neo4j 5.x (running locally or via Docker)
- pip (Python package manager)

### Install via pip

```bash
# Install latest release from PyPI
pip install socialseed-tasker

# Install specific version
pip install socialseed-tasker==0.8.1
```

### Install via git (Development)

```bash
# Clone the repository
git clone https://github.com/daironpf/socialseed-tasker.git
cd socialseed-tasker

# Create virtual environment (recommended)
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # Linux/Mac

# Install in editable mode
pip install -e .
```

### Command Not Found?

After installation, if `tasker` command is not found, add the Scripts directory to your PATH:

**Windows (PowerShell):**
```powershell
$env:Path += ";$env:USERPROFILE\AppData\Roaming\Python\Python314\Scripts"
tasker --help
```

**Windows (CMD):**
```cmd
set PATH=%PATH%;%USERPROFILE%\AppData\Roaming\Python\Python314\Scripts
tasker --help
```

**Linux/Mac:**
```bash
export PATH="$PATH:$HOME/.local/bin"
tasker --help
```

### Alternative: Use Python Module Directly

If the `tasker` command is not available, use Python module invocation:

```bash
# CLI
python -m socialseed_tasker.entrypoints.terminal_cli.app --help

# API
python -m socialseed_tasker.entrypoints.web_api
```

### Verify Installation

```bash
# Check CLI version
tasker --version
# or
python -m socialseed_tasker.entrypoints.terminal_cli.app --version

# Check CLI help
tasker --help

# Check API (requires Neo4j running)
curl http://localhost:8000/health
```

---

## Quick Start

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
# Expected: {"status":"healthy","version":"0.8.1","neo4j":"connected"}
```

### 3. Services Available

| Service | URL | Description |
|---------|-----|-------------|
| **Neo4j Browser** | `http://localhost:7474` | Graph database UI (neo4j/neoSocial) |
| **REST API** | `http://localhost:8000` | For AI agents to manage issues |
| **Frontend** | `http://localhost:8080` | Human UI (Kanban board & Interactive Graph View) |
| **API Docs** | `http://localhost:8000/docs` | OpenAPI documentation |
| **ReDoc** | `http://localhost:8000/redoc` | Alternative API documentation |

### 4. Try It Now - 30-Second Demo

```bash
# Set your API key
export TASKER_API_KEY=test-token
export TASKER_AUTH_ENABLED=true

# Create a component
COMP_ID=$(curl -s -X POST http://localhost:8000/api/v1/components \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TASKER_API_KEY" \
  -d '{"name":"backend","project":"my-app"}' | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Create an issue in that component
ISSUE_ID=$(curl -s -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TASKER_API_KEY" \
  -d "{\"title\":\"Fix login bug\",\"component_id\":\"$COMP_ID\",\"priority\":\"HIGH\"}" \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

# Link them: Fix login bug depends on Add unit tests
DEP_ID=$(curl -s -X POST http://localhost:8000/api/v1/issues \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TASKER_API_KEY" \
  -d "{\"title\":\"Add unit tests\",\"component_id\":\"$COMP_ID\"}" \
  | python -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")

curl -s -X POST "http://localhost:8000/api/v1/issues/$ISSUE_ID/dependencies" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TASKER_API_KEY" \
  -d "{\"depends_on_id\":\"$DEP_ID\"}"
```

### 5. Explore the Graph

Open **http://localhost:7474** in your browser and run this Cypher query to visualize your data:

```cypher
MATCH (i:Issue)-[:BELONGS_TO]->(c:Component)
RETURN i, c
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `TASKER_NEO4J_USER` | `neo4j` | Neo4j username |
| `TASKER_NEO4J_PASSWORD` | (none) | Neo4j password (required) |
| `API_PORT` | `8000` | API server port |
| `TASKER_API_KEY` | (none) | API key for authentication |
| `TASKER_AUTH_ENABLED` | `false` | Enable API authentication |
| `TASKER_DEMO_MODE` | `false` | Load demo data on startup |
| `TASKER_RATE_LIMIT_ENABLED` | `false` | Enable rate limiting |
| `TASKER_RATE_LIMIT_PER_MINUTE` | `100` | Requests per minute limit |
| `TASKER_SLOW_REQUEST_THRESHOLD` | `0.5` | Log requests slower than this (seconds) |
| `TASKER_ENABLE_PERF_LOGGING` | `true` | Enable performance monitoring |

---

## Performance Monitoring

All API responses include timing information:

```bash
# Get response with timing header
curl -v http://localhost:8000/api/v1/issues 2>&1 | grep X-Response-Time
# Output: X-Response-Time-Ms: 45.23
```

Slow requests (>500ms by default) are logged:

```
WARNING - Slow request: GET /api/v1/analyze/impact took 523.45ms (threshold: 500.00ms)
```

---

## REST API Reference

### Base URL
```
http://localhost:8000/api/v1
```

### Authentication

Set `TASKER_API_KEY` and `TASKER_AUTH_ENABLED=true` for production authentication.

```bash
# Example with authentication
curl -H "Authorization: Bearer your-secret-key" http://localhost:8000/api/v1/issues
```

### Performance Targets

| Endpoint | Target | Notes |
|----------|--------|-------|
| GET /issues | <100ms | Indexed queries |
| GET /issues/{id} | <50ms | Unique constraint lookup |
| POST /analyze/impact | <500ms | BFS with depth limit (3) |
| GET /graph/dependencies | <200ms | Index-based traversal |

### Key Endpoints

- **Issues**: Create, read, update, delete, close
- **Components**: Organize issues by service/module
- **Dependencies**: Link issues with [:DEPENDS_ON] relationships
- **Analysis**: Impact analysis, root cause detection
- **Projects**: Aggregate statistics by project
- **Health**: Neo4j connectivity status

For complete endpoint documentation, visit **http://localhost:8000/docs**

---

## Docker Compose

```bash
# Start everything
docker compose up -d

# View logs
docker compose logs -f

# Stop everything (data persists)
docker compose down

# Stop and remove all data
docker compose down -v
```

---

## Isolated Testing (Black-Box Evaluation)

For running isolated tests without the full stack:

### Quick Start (API + Neo4j Only)

```bash
# 1. Create isolated test directory
mkdir real-test && cd real-test

# 2. Start only Neo4j (minimal setup)
cp ../docker-compose-minimal.yml .
docker compose up -d

# 3. Wait for Neo4j to be ready
sleep 15

# 4. Verify connectivity
docker exec real-test-tasker-db-1 cypher-shell -u neo4j -p neoSocial "RETURN 1"
```

### Full Stack Isolated Testing

```bash
# 1. Create isolated test directory
mkdir real-test && cd real-test

# 2. Copy required files
cp ../docker-compose.yml .
cp ../Dockerfile .
cp -r ../frontend .
cp ../nginx.conf ./frontend/ 2>/dev/null || true

# 3. Install package
python -m venv venv
source venv/Scripts/activate  # Windows
# or: source venv/bin/activate  # Linux/Mac
pip install -e ..

# 4. Build and start services
docker compose build
docker compose up -d
```

### Required Files for Full Stack

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Service orchestration |
| `Dockerfile` | API container build |
| `frontend/` | Frontend source (Dockerfile, nginx.conf, dist/) |

---

## Docker Troubleshooting

### Common Issues

**`/frontend/package.json: not found`**
- Solution: Copy the `frontend/` directory or use `docker-compose-minimal.yml`

**`host not found in upstream "tasker-api"`**
- Solution: Update `nginx.conf` to use `host.docker.internal:8000`

**Neo4j container not healthy**
```bash
# Check logs
docker compose logs tasker-db

# Reset Neo4j data
docker compose down -v
docker compose up -d
```

**Port already in use**
```bash
# Find what's using the port
netstat -ano | findstr :7474  # Windows
# lsof -i :7474  # Linux/Mac

# Stop the conflicting service or change port in docker-compose.yml
```

**`tasker` command not found after pip install**
```bash
# Windows: Add Scripts to PATH
$env:Path += ";$env:USERPROFILE\AppData\Roaming\Python\Python314\Scripts"

# Linux/Mac: Add bin to PATH
export PATH="$PATH:$HOME/.local/bin"

# Or use Python module directly
python -m socialseed_tasker.entrypoints.terminal_cli.app --help
```

---

## Architecture

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
│ • Performance Monitoring  │
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

## Related Documentation

- **[CLI Reference](#)** - Command-line interface
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API endpoint reference
- **[VERSIONS.md](VERSIONS.md)** - Release milestones and feature checklists
- **[ROADMAP.md](ROADMAP.md)** - Strategic roadmap and future features
- **[SECURITY.md](SECURITY.md)** - Security policy and best practices
- **[Development](#)** - Running tests, contributing

---

## License

Apache 2.0 - See LICENSE file for details.