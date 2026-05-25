# Quick Start Guide

Get up and running with Tasker in 5 minutes.

---

## 1. Install (2 minutes)

### Prerequisites

Make sure you have:
- Python 3.11+
- Docker and Docker Compose

### Installation

```bash
# Clone repository
git clone https://github.com/daironpf/socialseed-tasker.git
cd socialseed-tasker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# OR
.\.venv\Scripts\activate  # Windows

# Install package
pip install -e ".[dev]"
```

**Verify:**
```bash
tasker --version
```

---

## 2. Start Infrastructure (1 minute)

Choose one based on your use case:

### Option A: Development (Direct Mode)

```bash
# Start only the database
docker compose up -d tasker-db

# Wait for startup
sleep 5

# Verify
curl http://localhost:8000/health
```

### Option B: Testing (API Mode)

```bash
# Start database + API server
docker compose --profile api up -d

# Wait for startup
sleep 10

# Verify
curl http://localhost:8888/health
```

---

## 3. Configure (1 minute)

### Direct Mode

```bash
export TASKER_MODE=direct
export TASKER_NEO4J_URI=bolt://localhost:7687
export TASKER_NEO4J_USER=neo4j
export TASKER_NEO4J_PASSWORD=neoSocial
```

### API Mode

```bash
export TASKER_MODE=api
export TASKER_API_URL=http://localhost:8888
```

---

## 4. Create First Project (1 minute)

```bash
# Create a component (project module)
tasker component create my-app -p demo

# Create an issue
tasker issue create "Add authentication" -c my-app -p HIGH

# List issues
tasker issue list

# View issue details
tasker issue show issue-<id>
```

---

## 5. Try Key Features (Optional - 5 more minutes)

### Create Dependencies

```bash
# Create another issue
tasker issue create "Setup database" -c my-app -p CRITICAL

# Create a dependency (first issue depends on second)
tasker dependency add issue-1 --depends-on issue-2

# Check what blocks issue-1
tasker dependency chain issue-1
```

### Analyze Impact

```bash
# Analyze impact of closing issue-2
tasker analyze impact issue-2
```

### Check Status

```bash
# View system status
tasker status --check-connectivity
```

---

## Common First Tasks

### Task 1: List All Components

```bash
tasker component list
```

### Task 2: Create Multiple Issues

```bash
tasker issue create "Feature: Login" -c my-app -p HIGH
tasker issue create "Bug: Dashboard slow" -c my-app -p MEDIUM
tasker issue create "Docs: API guide" -c my-app -p LOW
```

### Task 3: Assign and Track

```bash
# List all issues
tasker issue list

# Update issue status
tasker issue update issue-1 -s IN_PROGRESS

# Close when done
tasker issue close issue-1
```

### Task 4: View Blocked Issues

```bash
# See what can't be worked on yet
tasker dependency blocked

# Trace dependencies
tasker dependency chain issue-blocked
```

---

## What's Next?

| Interest | Read |
|----------|------|
| **All CLI commands** | [CLI Commands Reference](./cli-commands-reference.md) |
| **REST API** | [API Endpoints](./api-endpoints.md) |
| **Configuration** | [Configuration Reference](./configuration-reference.md) |
| **Modes (Direct vs API)** | [Dual Mode Guide](./dual-mode-guide.md) |
| **Help/Issues** | [FAQ](./faq.md) • [Troubleshooting](./troubleshooting.md) |

---

## Quick Command Reference

```bash
# Components
tasker component create <name> -p <project>
tasker component list
tasker component show <id>
tasker component delete <id>

# Issues  
tasker issue create <title> -c <component> -p <priority>
tasker issue list
tasker issue show <id>
tasker issue close <id>

# Dependencies
tasker dependency add <issue> --depends-on <other>
tasker dependency blocked
tasker dependency chain <issue>

# Info
tasker status
tasker help
tasker version
```

---

## Troubleshooting

### "Command not found: tasker"

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR
.\.venv\Scripts\activate  # Windows
```

### "Connection refused"

```bash
# Check infrastructure is running
docker compose ps

# Or start it
docker compose up -d
```

### "Neo4j password rejected"

```bash
# Verify password is set correctly
echo $TASKER_NEO4J_PASSWORD

# Or use the default
export TASKER_NEO4J_PASSWORD=neoSocial
```

---

## Full Guides

- **[Installation](./installation.md)** — Detailed setup for all platforms
- **[Configuration](./configuration-reference.md)** — All environment variables
- **[CLI Commands](./cli-commands-reference.md)** — Every command with examples
- **[API Reference](./api-endpoints.md)** — REST API contract
- **[FAQ](./faq.md)** — Common questions
