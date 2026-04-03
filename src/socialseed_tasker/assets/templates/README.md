# SocialSeed Tasker - Injected Infrastructure

This directory contains the Tasker management layer for this project.

## Structure

```
tasker/
├── skills/           # AI Agent skills for Tasker API interaction
├── configs/          # Local configuration (.env)
└── docker-compose.yml # Neo4j database for local development
```

## Quick Start

### 1. Start the database

```bash
# Local mode (Docker)
docker compose up -d

# Check health
docker compose ps
```

### 2. Configure environment

```bash
cp configs/.env.example configs/.env
# Edit configs/.env with your settings
```

### 3. Update skills

```bash
# Pull latest skill templates from the installed library
tasker init --force
```

### 4. Use the skills

The Python modules in `skills/` can be imported directly by AI agents
or scripts in this project. They communicate with the Tasker REST API
via HTTP - no direct imports of the Tasker core are needed.

```python
import sys
sys.path.insert(0, "tasker/skills")
from task_skill import create_issue, list_issues

# Create an issue
result = create_issue("Implement feature X", component_id="<uuid>")
```

## Switching to Neo4j Aura

Edit `configs/.env` and change the connection URI:

```bash
# Comment out LOCAL
# TASKER_NEO4J_URI=bolt://localhost:7689

# Uncomment and configure AURA
TASKER_NEO4J_URI=bolt+s://your-aura-id.databases.neo4j.io:7687
TASKER_NEO4J_PASSWORD=your_aura_password
```
