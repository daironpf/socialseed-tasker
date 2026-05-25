# CLI Dual Mode: Direct vs API

The Tasker CLI supports two operation modes to accommodate different deployment and testing scenarios:

- **Direct Mode**: Direct connection to Neo4j via Bolt protocol
- **API Mode**: HTTP calls to a FastAPI backend server

Choose the mode that best fits your workflow and infrastructure constraints.

---

## Mode Overview

### Direct Mode (default)

**When to use:**
- Local development and testing
- Direct database access is available
- Minimal latency requirement
- Testing without running the API server

**Requirements:**
- Neo4j database accessible via Bolt
- Neo4j driver connection credentials

**Connection Flow:**
```
CLI → Bolt Protocol → Neo4j Database
```

### API Mode

**When to use:**
- Production deployment (client-server architecture)
- API server provides unified interface
- Authentication via API tokens
- Multi-tenant or multi-environment setups
- Integration testing via API contract

**Requirements:**
- FastAPI backend running and accessible
- Optional: API authentication key

**Connection Flow:**
```
CLI → HTTP/REST → FastAPI Backend → Neo4j Database
```

---

## Configuration

### Method 1: Command-Line Variable

Set the mode via environment variable (highest priority):

```bash
# Direct mode (default)
tasker component list

# Explicitly set Direct mode
TASKER_MODE=direct tasker component list

# API mode
TASKER_MODE=api tasker component list
TASKER_MODE=api TASKER_API_URL=http://api.example.com tasker component list
```

### Method 2: Configuration File

Create or edit `.agent/configs/tasker.yml`:

```yaml
# Operation mode: "direct" or "api"
mode: direct

# --- API mode settings ---
api_url: http://localhost:8888
api_key: your-api-key-here  # Optional, for Bearer token auth
api_timeout: 10              # Seconds

# --- Direct mode settings ---
neo4j_uri: bolt://localhost:7687
neo4j_user: neo4j
neo4j_password: your-password
```

**Configuration Resolution Order:**
1. Environment variables (`TASKER_MODE`, `TASKER_API_URL`, etc.)
2. `.agent/configs/tasker.yml` file
3. Built-in defaults

### Method 3: Interactive Setup

Initialize configuration interactively:

```bash
tasker init
```

This prompts you to choose a mode and saves settings to `.agent/configs/tasker.yml`.

---

## Environment Variables

### Common to Both Modes

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_MODE` | `direct` | Operation mode: `direct` or `api` |

### Direct Mode Only

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt connection string |
| `TASKER_NEO4J_USER` | `neo4j` | Neo4j username |
| `TASKER_NEO4J_PASSWORD` | *(none)* | Neo4j password |

### API Mode Only

| Variable | Default | Description |
|----------|---------|-------------|
| `TASKER_API_URL` | `http://localhost:8888` | FastAPI backend base URL |
| `TASKER_API_KEY` | *(none)* | Bearer token for authentication (optional) |
| `TASKER_API_TIMEOUT` | `10` | HTTP request timeout in seconds |

---

## Usage Examples

### Direct Mode: Local Development

```bash
# Configure for local Neo4j
export TASKER_NEO4J_URI=bolt://localhost:7687
export TASKER_NEO4J_USER=neo4j
export TASKER_NEO4J_PASSWORD=mypassword

# Run commands (uses direct Neo4j connection)
tasker component list
tasker issue create "Fix login bug" -c auth -p HIGH
tasker issue show <issue-id>
```

### API Mode: Testing Against Server

```bash
# Configure for local API server
export TASKER_MODE=api
export TASKER_API_URL=http://localhost:8888

# Run the same commands (now via API)
tasker component list
tasker issue create "Fix login bug" -c auth -p HIGH
tasker issue show <issue-id>
```

### API Mode: Production with Token

```bash
# Configure for production API with authentication
export TASKER_MODE=api
export TASKER_API_URL=https://tasker.example.com
export TASKER_API_KEY=sk-abc123def456ghi789

# Commands use authenticated API calls
tasker component list
tasker issue create "Deploy feature X" -c deployment -p CRITICAL
```

### Switching Between Modes

```bash
# Save Direct mode config
cat > .agent/configs/tasker.yml << EOF
mode: direct
neo4j_uri: bolt://localhost:7687
neo4j_user: neo4j
neo4j_password: neoSocial
EOF

# Use Direct mode
tasker component list

# Override with API mode
TASKER_MODE=api TASKER_API_URL=http://localhost:8888 tasker component list

# Switch to API in config file
cat > .agent/configs/tasker.yml << EOF
mode: api
api_url: http://localhost:8888
api_timeout: 10
EOF

# Now all commands use API mode by default
tasker component list
```

---

## All Commands Work in Both Modes

Every Tasker CLI command works identically in both modes. The backend is transparent to the user:

```bash
# These work the same in both Direct and API modes:
tasker component create <name> -p <project>
tasker component list
tasker component show <id>
tasker issue create <title> -c <component> -p <priority>
tasker issue list
tasker dependency add <issue> --depends-on <dep>
tasker analyze root-cause <issue>
tasker code-graph scan <path>
```

---

## Docker Compose for API Mode

### Quick Start with API Backend

```bash
# Start only database
docker compose up -d

# OR start database + API server
docker compose --profile api up -d

# OR start full stack (database + API + frontend board)
docker compose --profile full up -d

# Verify API is running
curl http://localhost:8888/health
```

### docker-compose Services by Profile

| Service | Profile | Purpose |
|---------|---------|---------|
| `tasker-db` | *(none)* | Neo4j database (always runs) |
| `tasker-api` | `api`, `full` | FastAPI backend |
| `tasker-board` | `full` | Frontend UI (optional) |

---

## Error Handling

### Direct Mode Issues

**Neo4j Connection Refused**
```
Error: Could not connect to bolt://localhost:7687
```
→ Check Neo4j is running: `docker compose up -d`

**Authentication Failed**
```
Error: InvalidAuthorizationException
```
→ Verify `TASKER_NEO4J_USER` and `TASKER_NEO4J_PASSWORD`

### API Mode Issues

**API Server Unreachable**
```
Error: Connection refused for http://localhost:8888
```
→ Start API: `docker compose --profile api up -d`

**API Health Check Failed**
```
Error: API health check failed
```
→ Verify API is responding: `curl http://localhost:8888/health`

**Authentication Failed (401)**
```
Error: AuthenticationError
```
→ Check your `TASKER_API_KEY` if API requires authentication

**HTTP Timeout**
```
Error: Connection timeout after 10s
```
→ Increase timeout: `TASKER_API_TIMEOUT=30 tasker component list`

---

## Architecture

The dual-mode design uses **hexagonal architecture** (ports & adapters):

```
┌─────────────────────────────────────────────────┐
│              Tasker CLI Commands                 │
│  (component create, issue list, dependency...) │
└────────────────┬────────────────────────────────┘
                 │ (TaskRepositoryInterface)
                 ├─────────────────────────────────┐
                 ↓                                 ↓
        ┌──────────────────┐            ┌──────────────────┐
        │   Direct Adapter │            │    API Adapter   │
        │ (Neo4jRepository)│            │(ApiTaskRepository│
        └────────┬─────────┘            └────────┬─────────┘
                 ↓                                ↓
        ┌──────────────────┐            ┌──────────────────┐
        │  Neo4j Driver    │            │   HttpClient     │
        │  (Bolt Protocol) │            │  (REST API)      │
        └────────┬─────────┘            └────────┬─────────┘
                 ↓                                ↓
        ┌──────────────────┐            ┌──────────────────┐
        │ Neo4j Database   │            │ FastAPI Backend  │
        └──────────────────┘            └──────────────────┘
```

The `Container` dependency injection system routes to the correct adapter based on `TASKER_MODE`.

---

## Migration from Direct to API Mode

If you're switching from Direct to API mode:

1. **Ensure API server is running**
   ```bash
   docker compose --profile api up -d
   ```

2. **Verify API health**
   ```bash
   curl http://localhost:8888/health
   ```

3. **Update configuration**
   ```bash
   export TASKER_MODE=api
   export TASKER_API_URL=http://localhost:8888
   ```

4. **Test commands work**
   ```bash
   tasker component list
   tasker issue list
   ```

5. **Update your `.agent/configs/tasker.yml`** to persist the change

---

## Testing Both Modes

The test suite includes integration tests that verify both modes work correctly:

```bash
# Run all tests
pytest

# Run only CLI dual-mode tests
pytest tests/integration/test_cli_modes.py -v

# Test Direct mode
TASKER_MODE=direct pytest tests/integration/test_cli_modes.py -v

# Test API mode (requires API server running)
TASKER_MODE=api pytest tests/integration/test_cli_modes.py -v
```

---

## FAQ

**Q: Which mode should I use?**
A: Use `direct` for development/testing. Use `api` for production or when you need a unified interface.

**Q: Can I switch modes at runtime?**
A: Yes, set `TASKER_MODE` env var or edit `.agent/configs/tasker.yml` and re-run commands.

**Q: Does API mode require authentication?**
A: No, but it's recommended. Use `TASKER_API_KEY` for Bearer token auth.

**Q: What if config file is missing?**
A: Built-in defaults are used: Direct mode, localhost Neo4j/API.

**Q: Can I use both modes simultaneously?**
A: Yes, but they use independent backend connections. Data isn't shared between modes.

**Q: How do I verify which mode is active?**
A: Enable debug logging: `TASKER_LOG_LEVEL=DEBUG tasker component list`

---

## See Also

- [README.md](../README.md) - Project overview
- [API_REFERENCE.md](./API_REFERENCE.md) - REST API endpoints
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development setup
