# Installation and Setup Guide

Complete step-by-step guide to install and configure Tasker for your environment.

## System Requirements

| Component | Requirement |
|-----------|-------------|
| **Python** | 3.11 or higher |
| **Docker** | 20.10+ (for containerized backend) |
| **Docker Compose** | 2.0+ |
| **Disk Space** | 2GB+ (for Neo4j database) |
| **Memory** | 2GB+ (minimum 4GB recommended) |
| **OS** | macOS, Linux, or Windows (with WSL2) |

### Python Installation

**macOS (Homebrew)**
```bash
brew install python@3.11
python3.11 --version
```

**Ubuntu/Debian**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
python3.11 --version
```

**Windows**
Download from [python.org](https://www.python.org/downloads/) and run installer

---

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/daironpf/socialseed-tasker.git
cd socialseed-tasker
```

### 2. Create Virtual Environment

**macOS/Linux**
```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

### 4. Install Package and Dependencies

```bash
# Install in development mode (recommended for local development)
pip install -e ".[dev]"

# OR install production dependencies only
pip install -r requirements.txt
```

**Installation output should show:**
```
Successfully installed socialseed-tasker
...
✓ httpx>=0.25.0
✓ pyyaml>=6.0
✓ fastapi>=0.109.0
✓ neo4j>=5.15.0
```

### 5. Verify Installation

```bash
# Check Python environment
python --version  # Should be 3.11+
pip list | grep -E "tasker|httpx|pyyaml|fastapi"

# Check tasker CLI
tasker --version
tasker --help
```

---

## Infrastructure Setup

### Option A: Quick Start (All-in-One)

```bash
# Start database + API server + frontend
docker compose --profile full up -d

# Wait for services to initialize
sleep 10

# Verify all services
curl http://localhost:8000/health  # Neo4j
curl http://localhost:8888/health  # API
curl http://localhost:3000/health  # Frontend (if running)
```

### Option B: Development (Database Only)

For direct Neo4j connection during development:

```bash
# Start only the database
docker compose up -d tasker-db

# Wait for Neo4j to initialize
sleep 5

# Verify database is running
curl http://localhost:8000/health
```

### Option C: Testing (Database + API)

For testing API mode:

```bash
# Start database and API server
docker compose --profile api up -d

# Wait for services
sleep 10

# Verify
curl http://localhost:8000/health
curl http://localhost:8888/health
```

### Option D: Manual (No Docker)

If Docker is not available:

```bash
# Install Neo4j locally (requires separate installation)
# Then configure connection:
export TASKER_NEO4J_URI=bolt://localhost:7687
export TASKER_NEO4J_USER=neo4j
export TASKER_NEO4J_PASSWORD=yourpassword
```

---

## Configure Your Mode

### Direct Mode (Local Development)

Best for local development with direct database access.

**Step 1: Set environment variables**
```bash
export TASKER_MODE=direct
export TASKER_NEO4J_URI=bolt://localhost:7687
export TASKER_NEO4J_USER=neo4j
export TASKER_NEO4J_PASSWORD=neoSocial
```

**Step 2: Or create `.agent/configs/tasker.yml`**
```yaml
mode: direct
neo4j_uri: bolt://localhost:7687
neo4j_user: neo4j
neo4j_password: neoSocial
```

**Step 3: Verify**
```bash
tasker component list
# Should return: (empty or existing components)
```

### API Mode (Testing/Production)

Best for server deployments and integrated testing.

**Step 1: Start API server**
```bash
docker compose --profile api up -d
sleep 10
```

**Step 2: Set environment variables**
```bash
export TASKER_MODE=api
export TASKER_API_URL=http://localhost:8888
export TASKER_API_KEY=  # Leave empty if no auth
```

**Step 3: Or create `.agent/configs/tasker.yml`**
```yaml
mode: api
api_url: http://localhost:8888
api_timeout: 10
```

**Step 4: Verify**
```bash
curl http://localhost:8888/health
tasker component list
```

---

## First-Time Setup with `tasker init`

Interactive setup wizard:

```bash
tasker init
```

This will prompt you to:
1. Choose operation mode (Direct or API)
2. Configure Neo4j connection (Direct mode) or API URL (API mode)
3. Set authentication if needed
4. Save configuration to `.agent/configs/tasker.yml`

**Output:**
```
✓ Configuration saved to .agent/configs/tasker.yml
✓ Mode: direct
✓ Neo4j: bolt://localhost:7687
✓ Ready to use!
```

---

## Verify Everything Works

### Health Checks

```bash
# Check database (if using Direct mode or API uses DB)
curl http://localhost:8000/health
# Response: {"status": "ok"}

# Check API (if using API mode)
curl http://localhost:8888/health
# Response: {"status": "ok"}

# Check CLI
tasker component list
# Response: [] (empty list if no components yet)
```

### Create Test Data

```bash
# Create a component
tasker component create test-component -p demo

# Verify it was created
tasker component list
# Should show: test-component

# Create an issue
tasker issue create "Test issue" -c test-component -p HIGH

# Verify
tasker issue list
# Should show: Test issue
```

---

## Troubleshooting Installation

### Issue: `ModuleNotFoundError: No module named 'socialseed_tasker'`

**Cause:** Package not installed properly

**Solution:**
```bash
# Ensure virtual environment is activated
which python  # Should show path in .venv/

# Reinstall
pip install -e ".[dev]"

# Verify
python -c "import socialseed_tasker; print('OK')"
```

### Issue: `Command 'tasker' not found`

**Cause:** Virtual environment not activated or package not installed

**Solution:**
```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.\.venv\Scripts\Activate.ps1  # Windows PowerShell

# Reinstall if needed
pip install -e "."

# Check installation
which tasker
tasker --help
```

### Issue: `ModuleNotFoundError: No module named 'pyyaml'`

**Cause:** Missing dependency

**Solution:**
```bash
pip install pyyaml>=6.0
pip install -r requirements.txt  # Install all deps
```

### Issue: `Connection refused to bolt://localhost:7687`

**Cause:** Neo4j database not running

**Solution:**
```bash
# Check if running
docker compose ps

# Start it
docker compose up -d tasker-db

# Wait for startup
sleep 10

# Verify
curl http://localhost:8000/health
```

### Issue: `Connection refused to http://localhost:8888`

**Cause:** API server not running

**Solution:**
```bash
# Start API
docker compose --profile api up -d

# Wait for startup
sleep 10

# Verify
curl http://localhost:8888/health
```

### Issue: Permission denied on `activate` script

**Cause:** Script file permissions on Linux/macOS

**Solution:**
```bash
chmod +x .venv/bin/activate
source .venv/bin/activate
```

---

## Docker-Specific Setup

### Check Running Containers

```bash
docker compose ps

# Output should show:
# NAME              STATUS
# tasker-db         Up 2 minutes
# tasker-api        Up 1 minute (if --profile api)
# tasker-board      Up 1 minute (if --profile full)
```

### View Logs

```bash
# Database logs
docker compose logs tasker-db -f

# API logs
docker compose logs tasker-api -f

# All logs
docker compose logs -f
```

### Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart tasker-api

# Full restart (stop and start)
docker compose down
docker compose up -d
```

### Clean Up

```bash
# Stop all services
docker compose stop

# Remove containers and volumes (WARNING: deletes data!)
docker compose down -v

# Remove everything including images
docker compose down -v --remove-orphos --rmi all
```

---

## Development Tools

### Install Dev Dependencies

```bash
pip install -e ".[dev]"
```

This installs:
- pytest, pytest-asyncio, pytest-cov (testing)
- ruff, mypy (linting)
- mkdocs (documentation)

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_container.py

# With coverage
pytest --cov=socialseed_tasker tests/

# Show coverage report
pytest --cov=socialseed_tasker --cov-report=html tests/
# Open: htmlcov/index.html
```

### Linting and Type Checking

```bash
# Format code
ruff format src/ tests/

# Check for issues
ruff check src/

# Type checking
mypy src/socialseed_tasker
```

### Build Documentation

```bash
# If using mkdocs
mkdocs serve  # Local preview at http://localhost:8000

# Build static HTML
mkdocs build
```

---

## Environment-Specific Setup

### For Windows WSL2

```bash
# Inside WSL2 terminal
wsl --install Ubuntu

# Inside Ubuntu:
sudo apt update
sudo apt install python3.11 python3.11-venv docker.io docker-compose

# Continue with standard Linux installation
```

### For macOS ARM64 (Apple Silicon)

```bash
# Ensure correct Python version
arch -arm64 brew install python@3.11

# Continue with standard installation
```

### For Production (Docker)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY src/socialseed_tasker src/

# Run CLI
ENTRYPOINT ["tasker"]
```

---

## Next Steps

After installation:

1. **[Quick Start](./quick-start.md)** — Run your first commands (5 min)
2. **[CLI Commands Reference](./cli-commands-reference.md)** — Learn all commands
3. **[Dual Mode Guide](./dual-mode-guide.md)** — Understand Direct vs API modes
4. **[Configuration Reference](./configuration-reference.md)** — Advanced configuration

---

## Getting Help

- **[FAQ](./faq.md)** — Common questions
- **[Troubleshooting](./troubleshooting.md)** — Debug issues
- **[GitHub Issues](https://github.com/daironpf/socialseed-tasker/issues)** — Report problems
