# FAQ - Frequently Asked Questions

Quick answers to common questions about Tasker.

---

## Installation & Setup

### Q: What are the system requirements?

**A:** 
- Python 3.11 or higher
- Docker and Docker Compose (for infrastructure)
- 2GB+ disk space
- 2GB+ RAM (4GB recommended)

[See detailed system requirements →](./installation.md#system-requirements)

---

### Q: How do I install Tasker?

**A:** Quick version:

```bash
git clone https://github.com/daironpf/socialseed-tasker.git
cd socialseed-tasker
python -m venv .venv
source .venv/bin/activate  # or .\.venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

[See full installation guide →](./installation.md)

---

### Q: Do I need Docker?

**A:** Not necessarily:
- **Direct Mode**: Requires Neo4j accessible via Bolt (can be local or remote)
- **API Mode**: Requires FastAPI backend (can use Docker or install locally)

Docker Compose makes it easiest, but you can install Neo4j and FastAPI separately.

---

### Q: How do I know if installation worked?

**A:**
```bash
tasker --version
tasker status --check-connectivity
```

If both run without errors, you're good to go!

---

## Operation Modes

### Q: What's the difference between Direct and API mode?

**A:**

| Aspect | Direct | API |
|--------|--------|-----|
| **Connection** | CLI → Neo4j Bolt | CLI → API → Neo4j |
| **Best For** | Local development | Production, teams |
| **Setup** | Simpler | Slightly more complex |
| **Security** | Direct DB access needed | Single access point |
| **Performance** | Slightly faster | Network overhead |
| **Default** | Yes | No |

[See detailed comparison →](./dual-mode-guide.md)

---

### Q: Which mode should I use?

**A:**
- **Direct**: You're developing locally and have direct database access
- **API**: You're deploying to production or testing with the API server

You can switch between modes anytime by changing `TASKER_MODE`.

---

### Q: Can I use both modes simultaneously?

**A:** Yes, but they use independent backend connections. Data created in one mode is accessible from the other (same database), but connection configuration is separate.

---

### Q: How do I switch between modes?

**A:** Easy! Just change the environment variable:

```bash
# Current mode (default: direct)
tasker component list

# Switch to API mode
TASKER_MODE=api tasker component list

# Back to Direct
tasker component list
```

Or edit `.agent/configs/tasker.yml` to make it permanent.

---

## Configuration

### Q: Where does Tasker look for configuration?

**A:** In this order (highest priority first):
1. Environment variables (`TASKER_MODE`, `TASKER_API_URL`, etc.)
2. `.agent/configs/tasker.yml` file
3. Built-in defaults

---

### Q: How do I set up configuration?

**A:** Three ways:

**Option 1: Interactive**
```bash
tasker init  # Prompts you
```

**Option 2: Environment variables**
```bash
export TASKER_MODE=api
export TASKER_API_URL=http://localhost:8888
```

**Option 3: Manual YAML file**
```bash
mkdir -p .agent/configs
cat > .agent/configs/tasker.yml << EOF
mode: api
api_url: http://localhost:8888
EOF
```

[See all configuration options →](./configuration-reference.md)

---

### Q: How do I use different configs for different projects?

**A:**
```bash
# Create separate config files
mkdir -p configs
cp .agent/configs/tasker.yml configs/project-a.yml
cp .agent/configs/tasker.yml configs/project-b.yml

# Edit each with different settings
nano configs/project-a.yml

# Use them
tasker --config configs/project-a.yml component list
tasker --config configs/project-b.yml component list
```

---

### Q: Can I keep secrets out of Git?

**A:** Absolutely! Best practice:

```bash
# Add to .gitignore
echo ".agent/configs/tasker.yml" >> .gitignore
echo ".env" >> .gitignore

# Create example file (safe to commit)
cp .agent/configs/tasker.yml .agent/configs/tasker.yml.example
# Edit example to remove secrets
git add .agent/configs/tasker.yml.example

# Each developer creates their own
cp .agent/configs/tasker.yml.example .agent/configs/tasker.yml
# Edit with local settings
```

---

## Using the CLI

### Q: How do I see all available commands?

**A:**
```bash
tasker --help
tasker help <command>  # For specific command
tasker help issue create  # For subcommand
```

[See full command reference →](./cli-commands-reference.md)

---

### Q: How do I create a component and issue?

**A:**
```bash
# Create component
tasker component create my-app -p demo

# Create issue for that component
tasker issue create "Add authentication" -c my-app -p HIGH

# List to verify
tasker component list
tasker issue list
```

---

### Q: How do I manage dependencies?

**A:**
```bash
# Create two issues first
tasker issue create "Setup database" -c my-app -p CRITICAL
tasker issue create "Add user table" -c my-app -p HIGH

# Make second depend on first (second blocked by first)
tasker dependency add issue-2 --depends-on issue-1

# View dependency chain
tasker dependency chain issue-2

# See all blocked issues
tasker dependency blocked
```

---

### Q: Can I export data from the CLI?

**A:** Yes! Use `--output` flag:

```bash
# JSON
tasker component list --output json > components.json

# CSV
tasker issue list --output csv > issues.csv

# Pipe to other tools
tasker component list --output json | jq '.[] | .name'
```

---

## REST API

### Q: Is there a REST API I can use instead of the CLI?

**A:** Yes! When running in API mode:

```bash
# Health check
curl http://localhost:8888/health

# List components
curl http://localhost:8888/api/v1/components

# Create issue
curl -X POST http://localhost:8888/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{"title":"My issue"}'
```

[See all API endpoints →](./api-endpoints.md)

---

### Q: Can I use the API from Python?

**A:** Yes, use the httpx library (already installed):

```python
import httpx

client = httpx.Client(base_url="http://localhost:8888")
resp = client.get("/api/v1/components")
components = resp.json()
```

Or use the Python package directly:

```python
from socialseed_tasker.application.container import Container

container = Container.from_env()
repo = container.get_repository()
components = repo.list_components()
```

---

## Database & Infrastructure

### Q: How do I start the database?

**A:**
```bash
# Just database
docker compose up -d tasker-db

# Database + API
docker compose --profile api up -d

# Full stack
docker compose --profile full up -d

# View status
docker compose ps
```

---

### Q: How do I stop the database?

**A:**
```bash
docker compose stop      # Keep data
docker compose down      # Remove containers
docker compose down -v   # Remove containers and data
```

---

### Q: Where is my data stored?

**A:** 
- In Docker volumes (managed by Docker Compose)
- In `.agent/data/` directory (local Neo4j installation)
- Query the database directly with Neo4j Browser at `http://localhost:8000`

---

### Q: Can I use a remote database?

**A:** Yes!

```bash
# Direct mode with remote Neo4j
export TASKER_MODE=direct
export TASKER_NEO4J_URI=bolt://db.example.com:7687
export TASKER_NEO4J_USER=your-user
export TASKER_NEO4J_PASSWORD=your-password

tasker component list
```

[See configuration options →](./configuration-reference.md)

---

## Troubleshooting

### Q: I get "Command not found: tasker"

**A:** Your virtual environment isn't activated:

```bash
# Activate it
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\activate   # Windows

# Then try again
tasker --help
```

---

### Q: I get "Connection refused"

**A:** Your database or API isn't running:

```bash
# Check what's running
docker compose ps

# Start it
docker compose up -d

# Wait a few seconds
sleep 5

# Verify
curl http://localhost:8000/health  # Neo4j
curl http://localhost:8888/health  # API
```

---

### Q: I get "Neo4j connection refused" or "Invalid credentials"

**A:**
```bash
# Check your settings
echo "URI: $TASKER_NEO4J_URI"
echo "USER: $TASKER_NEO4J_USER"
echo "PASS: $TASKER_NEO4J_PASSWORD"

# Verify database is running
docker compose logs tasker-db

# Check Neo4j directly
curl http://localhost:8000/health
```

---

### Q: I get "API health check failed"

**A:**
```bash
# Check API is running
docker compose logs tasker-api

# Verify connectivity
curl http://localhost:8888/health

# Check API configuration
echo $TASKER_API_URL
echo $TASKER_API_TIMEOUT
```

---

## Performance & Optimization

### Q: My commands are slow. How can I speed them up?

**A:**
- Direct Mode is faster than API Mode (no network overhead)
- Close and filter unnecessary data (`--limit`, `--filter`)
- Use API mode in production (better for scaling)

---

### Q: How many issues/components can Tasker handle?

**A:** Neo4j can handle millions of nodes. Most performance concerns are solved by:
- Proper indexing (handled automatically)
- Filtering and pagination in queries
- Using API mode for high-load scenarios

---

## Contributing & Support

### Q: Where can I report bugs?

**A:** [GitHub Issues](https://github.com/daironpf/socialseed-tasker/issues)

---

### Q: How can I contribute?

**A:** [Contributing Guide](../CONTRIBUTING.md)

---

### Q: Where can I get help?

**A:**
1. [This FAQ](./faq.md)
2. [Troubleshooting Guide](./troubleshooting.md)
3. [Full Documentation](./index.md)
4. [GitHub Issues](https://github.com/daironpf/socialseed-tasker/issues)

---

## More Questions?

Check the full documentation:
- [Installation Guide](./installation.md)
- [Quick Start](./quick-start.md)
- [CLI Commands Reference](./cli-commands-reference.md)
- [Configuration Reference](./configuration-reference.md)
- [API Endpoints](./api-endpoints.md)
- [Troubleshooting](./troubleshooting.md)
