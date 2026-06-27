# Dual-Mode Setup Guide

Complete guide for setting up and troubleshooting the Tasker CLI in both Direct and API modes.

---

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Virtual environment activated

---

## Initial Setup

### 1. Install Dependencies

```bash
pip install -e ".[dev]"

# Or just the required packages
pip install -r requirements.txt
```

**Troubleshooting:** 
- If you get `ModuleNotFoundError: No module named 'pyyaml'`, ensure `pyyaml>=6.0` is in `requirements.txt`
- If you get `ModuleNotFoundError: No module named 'httpx'`, ensure `httpx>=0.25.0` is in `requirements.txt` (not dev-only)

### 2. Start Infrastructure

```bash
# Start Neo4j database (required for Direct mode)
docker compose up -d tasker-db

# Start database + API server (for API mode)
docker compose --profile api up -d

# Start full stack (database + API + frontend)
docker compose --profile full up -d
```

### 3. Verify Setup

```bash
# Check database health
curl http://localhost:8000/health

# Check API server (if running --profile api)
curl http://localhost:8888/health
```

---

## Mode Setup

### Direct Mode Setup

**1. Set environment variables:**
```bash
export TASKER_MODE=direct
export TASKER_NEO4J_URI=bolt://localhost:7687
export TASKER_NEO4J_USER=neo4j
export TASKER_NEO4J_PASSWORD=neoSocial
```

**2. Or create `.agent/configs/tasker.yml`:**
```yaml
mode: direct
neo4j_uri: bolt://localhost:7687
neo4j_user: neo4j
neo4j_password: neoSocial
```

**3. Test it works:**
```bash
tasker component list
# Should return empty list or existing components from Neo4j
```

### API Mode Setup

**1. Ensure API server is running:**
```bash
docker compose --profile api up -d
```

**2. Set environment variables:**
```bash
export TASKER_MODE=api
export TASKER_API_URL=http://localhost:8888
export TASKER_API_KEY=  # Leave empty if no auth required
export TASKER_API_TIMEOUT=10
```

**3. Or create `.agent/configs/tasker.yml`:**
```yaml
mode: api
api_url: http://localhost:8888
api_key: your-api-key-here  # Optional
api_timeout: 10
```

**4. Verify API is accessible:**
```bash
curl http://localhost:8888/health
# Should return: {"status": "ok"}
```

**5. Test it works:**
```bash
tasker component list
# Should return components from API
```

---

## Common Setup Issues

### Issue: "ModuleNotFoundError: No module named 'pyyaml'"

**Cause:** `pyyaml` not installed, but configuration loading requires it.

**Solution:**
```bash
pip install pyyaml>=6.0

# Or add to requirements.txt and reinstall
pip install -r requirements.txt
```

**Workaround:** Use environment variables only (skip YAML file):
```bash
export TASKER_MODE=direct
export TASKER_NEO4J_URI=...
tasker component list  # YAML file loading is skipped, env vars used
```

### Issue: "Neo4j connection refused"

**Cause:** Neo4j database not running.

**Solution:**
```bash
# Start database
docker compose up -d tasker-db

# Wait a few seconds for it to initialize
sleep 5

# Verify it's running
curl http://localhost:8000/health
```

### Issue: "API server unreachable" (TASKER_MODE=api)

**Cause:** API server not running.

**Solution:**
```bash
# Start API server
docker compose --profile api up -d

# Wait for it to initialize
sleep 5

# Verify it's running
curl http://localhost:8888/health
```

### Issue: "Authentication failed" (API mode with token)

**Cause:** Invalid or missing API key.

**Solution:**
```bash
# Check your API key is correct
echo $TASKER_API_KEY

# If empty, either:
# 1. API doesn't require auth (remove TASKER_API_KEY)
# 2. Get correct API key from server admin

# Test without auth key
unset TASKER_API_KEY
tasker component list

# If that works, auth isn't required
```

### Issue: "YAML config file not found" (warnings)

**Cause:** `.agent/configs/tasker.yml` doesn't exist.

**Solution:**
```bash
# Create config directory
mkdir -p .agent/configs

# Copy example
cp src/socialseed_tasker/assets/templates/configs/tasker.yml.example .agent/configs/tasker.yml

# Edit with your settings
nano .agent/configs/tasker.yml
```

**Or use interactive setup:**
```bash
tasker init  # Prompts you and creates the file
```

### Issue: "Which mode am I using?"

**Solution:** Check active configuration:
```bash
# Enable debug logging
TASKER_LOG_LEVEL=DEBUG tasker component list

# Or check environment
echo "TASKER_MODE=${TASKER_MODE:-direct}"
echo "TASKER_API_URL=$TASKER_API_URL"
echo "TASKER_NEO4J_URI=$TASKER_NEO4J_URI"

# Or check config file
cat .agent/configs/tasker.yml 2>/dev/null || echo "No config file"
```

---

## Testing Both Modes

### Run Unit Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests for ApiRepository (mocked HTTP)
pytest tests/unit/test_api_repository.py -v

# Run all tests
pytest tests/ -v
```

### Run Integration Tests (requires infrastructure)

```bash
# Start infrastructure
docker compose --profile api up -d
sleep 5

# Run Direct mode tests
TASKER_MODE=direct pytest tests/integration/test_cli_modes.py -v

# Run API mode tests
TASKER_MODE=api pytest tests/integration/test_cli_modes.py -v
```

### Manual Testing

**Test Direct mode:**
```bash
export TASKER_MODE=direct
export TASKER_NEO4J_URI=bolt://localhost:7687
export TASKER_NEO4J_USER=neo4j
export TASKER_NEO4J_PASSWORD=neoSocial

# Run commands
tasker component create test-component -p demo
tasker component list
tasker component show test-component
```

**Test API mode:**
```bash
export TASKER_MODE=api
export TASKER_API_URL=http://localhost:8888

# Run same commands - should work identically
tasker component create test-component-api -p demo
tasker component list
tasker component show test-component-api
```

---

## Switching Modes at Runtime

### Method 1: Environment Variable

```bash
# Currently in Direct mode?
tasker component list

# Switch to API mode for one command
TASKER_MODE=api tasker component list

# Back to Direct
tasker component list
```

### Method 2: Update Config File

```bash
# Edit .agent/configs/tasker.yml
cat > .agent/configs/tasker.yml << 'EOF'
mode: api
api_url: http://localhost:8888
EOF

# Now all commands use API
tasker component list
```

### Method 3: Update Environment

```bash
# Current mode via env
echo $TASKER_MODE  # Empty = default = direct

# Switch to API permanently (this session)
export TASKER_MODE=api
export TASKER_API_URL=http://localhost:8888

# All subsequent commands use API
tasker component list
tasker issue list
```

---

## CI/CD Integration

### Testing Both Modes in CI

```yaml
# .github/workflows/test.yml example
jobs:
  test-direct-mode:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start database
        run: docker compose up -d tasker-db
      - name: Wait for database
        run: sleep 10
      - name: Run tests
        env:
          TASKER_MODE: direct
        run: pytest tests/integration/test_cli_modes.py -v

  test-api-mode:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start API server
        run: docker compose --profile api up -d
      - name: Wait for API
        run: |
          for i in {1..30}; do
            curl http://localhost:8888/health && break
            sleep 1
          done
      - name: Run tests
        env:
          TASKER_MODE: api
          TASKER_API_URL: http://localhost:8888
        run: pytest tests/integration/test_cli_modes.py -v
```

---

## Debugging

### Enable Debug Logging

```bash
# For a single command
TASKER_LOG_LEVEL=DEBUG tasker component list

# For all commands (set in environment)
export TASKER_LOG_LEVEL=DEBUG
tasker component list
tasker issue list
```

### Check Configuration Resolution

```bash
# Print resolved configuration (in Python)
python << 'EOF'
import os
from socialseed_tasker.config.mode_config import DualModeConfig

cfg = DualModeConfig.load()
print(f"Mode: {cfg.mode}")
print(f"API URL: {cfg.api_url}")
print(f"Neo4j URI: {cfg.neo4j_uri}")
print(f"Config loaded from: env > yaml > defaults")
EOF
```

### Test HTTP Connection (API mode)

```bash
# Check if API is reachable
curl -v http://localhost:8888/health

# With authentication header
curl -v -H "Authorization: Bearer $TASKER_API_KEY" \
     http://localhost:8888/api/v1/components

# Test with httpx (same as CLI uses)
python -c "
import httpx
client = httpx.Client(base_url='http://localhost:8888', timeout=10)
resp = client.get('/health')
print(f'Status: {resp.status_code}')
print(f'Body: {resp.json()}')
"
```

### Test Neo4j Connection (Direct mode)

```bash
# Check if Neo4j is reachable
curl http://localhost:8000/health

# Test with Neo4j driver directly
python << 'EOF'
from neo4j import GraphDatabase
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "neoSocial"))
try:
    with driver.session() as session:
        result = session.run("RETURN 1 as num")
        print(f"Connected! Result: {result.single()}")
finally:
    driver.close()
EOF
```

---

## Production Deployment

### API Mode in Production

```bash
# 1. Start API server with persistent database
docker compose --profile api up -d

# 2. Get API URL (could be same server or different host)
API_URL="https://tasker-api.example.com"

# 3. Generate API key (from server)
API_KEY="sk-prod-abc123def456..."

# 4. On client side, configure
export TASKER_MODE=api
export TASKER_API_URL=$API_URL
export TASKER_API_KEY=$API_KEY
export TASKER_API_TIMEOUT=30  # Longer timeout for prod

# 5. All CLI commands now use secure API
tasker component list
```

### Direct Mode in Production (Not Recommended)

```bash
# Direct connections to production Neo4j require:
# - Network security (firewall, VPN)
# - Strong authentication
# - Encrypted Bolt connections

export TASKER_MODE=direct
export TASKER_NEO4J_URI=bolt+s://prod-db.example.com:7687
export TASKER_NEO4J_USER=tasker-user
export TASKER_NEO4J_PASSWORD=$NEO4J_PASSWORD

# Not ideal for production: clients need direct DB access
# Prefer API mode for production
```

---

## See Also

- [docs/cli_modes.md](./cli_modes.md) - Dual-mode documentation
- [docs/api_contract.md](./api_contract.md) - API endpoints reference
- [README.md](../README.md) - Project overview
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Development setup
