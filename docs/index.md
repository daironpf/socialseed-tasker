---
layout: default
title: Documentation Index
---

# SocialSeed Tasker Documentation

Complete reference for using the Tasker CLI and API in both Direct and API modes.

## Quick Navigation

### Getting Started
- **[Installation Guide](./installation.md)** — Install and verify setup
- **[Quick Start](./quick-start.md)** — First 5 minutes with Tasker
- **[Configuration](./configuration.md)** — Configure Direct or API mode

### Core Concepts
- **[Dual Mode Guide](./dual-mode-guide.md)** — Direct vs API mode comparison
- **[Architecture](./architecture.md)** — Hexagonal design and component overview
- **[Graph Data Model](./graph-model.md)** — Neo4j schema and relationships

### Usage Guides
- **[CLI Commands Reference](./cli-commands-reference.md)** — All commands with examples
- **[API Endpoints Reference](./api-endpoints.md)** — REST API contract
- **[Configuration Reference](./configuration-reference.md)** — All env vars and YAML options

### Advanced Topics
- **[Code-as-Graph](./code-graph.md)** — Using code analysis features
- **[RAG & Reasoning](./rag-guide.md)** — AI reasoning integration
- **[Agent Integration](./agent-integration.md)** — Agent orchestration
- **[Deployment](./deployment.md)** — Production setup and best practices

### Troubleshooting
- **[FAQ](./faq.md)** — Frequently asked questions
- **[Troubleshooting](./troubleshooting.md)** — Common issues and solutions
- **[CI/CD Integration](./ci-cd.md)** — Testing in multiple modes

---

## Mode Quick Reference

### Direct Mode (Default)
```bash
# Direct connection to Neo4j
tasker component list
```
**Use when**: Local development, direct database access available

### API Mode
```bash
# Via REST API backend
TASKER_MODE=api tasker component list
```
**Use when**: Production, unified interface, multi-tenant

---

## Common Tasks

### Set Up Direct Mode (Local Development)
```bash
# 1. Start database
docker compose up -d tasker-db
sleep 5

# 2. Configure
export TASKER_MODE=direct
export TASKER_NEO4J_URI=bolt://localhost:7687
export TASKER_NEO4J_USER=neo4j
export TASKER_NEO4J_PASSWORD=neoSocial

# 3. Test
tasker component list
```

### Set Up API Mode (Testing/Production)
```bash
# 1. Start API server
docker compose --profile api up -d
sleep 5

# 2. Configure
export TASKER_MODE=api
export TASKER_API_URL=http://localhost:8888

# 3. Test
curl http://localhost:8888/health
tasker component list
```

### Create Your First Issue
```bash
# Create component
tasker component create myapp -p demo

# Create issue
tasker issue create "Add authentication" -c myapp -p HIGH

# View issue
tasker issue list
```

### Analyze Dependencies
```bash
# See what blocks this issue
tasker dependency blocked

# See dependency chain
tasker dependency chain issue-123

# Add a blocking dependency
tasker dependency add issue-456 --depends-on issue-789
```

---

## Installation

### Requirements
- Python 3.11+
- Docker & Docker Compose
- 2GB+ disk space for database

### Quick Install
```bash
# Clone repository
git clone https://github.com/daironpf/socialseed-tasker.git
cd socialseed-tasker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install package
pip install -e ".[dev]"

# Start infrastructure
docker compose --profile api up -d

# Initialize
tasker init
```

**→ See [Installation Guide](./installation.md) for detailed setup**

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `TASKER_MODE` | `direct` | Operation mode: `direct` or `api` |
| `TASKER_NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection (Direct mode) |
| `TASKER_NEO4J_USER` | `neo4j` | Neo4j username (Direct mode) |
| `TASKER_NEO4J_PASSWORD` | - | Neo4j password (Direct mode) |
| `TASKER_API_URL` | `http://localhost:8888` | API base URL (API mode) |
| `TASKER_API_KEY` | - | API authentication key (optional) |
| `TASKER_API_TIMEOUT` | `10` | API request timeout in seconds |

**→ See [Configuration Reference](./configuration-reference.md) for all options**

---

## All CLI Commands

### Component Management
```bash
tasker component create <name> -p <project>
tasker component list
tasker component show <id>
tasker component update <id>
tasker component delete <id>
```

### Issue Management
```bash
tasker issue create <title> -c <component> -p <priority>
tasker issue list
tasker issue show <id>
tasker issue close <id>
tasker issue delete <id>
```

### Dependencies
```bash
tasker dependency add <issue> --depends-on <dep>
tasker dependency remove <issue> --depends-on <dep>
tasker dependency chain <issue>
tasker dependency blocked
```

### Analysis
```bash
tasker analyze root-cause <issue>
tasker analyze impact <issue>
```

### Code-as-Graph
```bash
tasker code-graph scan <path>
tasker code-graph find <symbol>
tasker code-graph calls <function>
```

**→ See [CLI Commands Reference](./cli-commands-reference.md) for complete list with examples**

---

## REST API

### Health Check
```bash
curl http://localhost:8888/health
```

### List Components
```bash
curl http://localhost:8888/api/v1/components
```

### Create Issue
```bash
curl -X POST http://localhost:8888/api/v1/issues \
  -H "Content-Type: application/json" \
  -d '{"title":"My issue","priority":"HIGH"}'
```

**→ See [API Endpoints Reference](./api-endpoints.md) for complete contract**

---

## Get Help

- **[FAQ](./faq.md)** — Quick answers to common questions
- **[Troubleshooting](./troubleshooting.md)** — Debug common issues
- **[GitHub Issues](https://github.com/daironpf/socialseed-tasker/issues)** — Report bugs
- **[Contributing](../CONTRIBUTING.md)** — Contribute code or docs

---

## Learn More

- **[Project README](../README.md)** — Overview and features
- **[Architecture Deep Dive](./architecture.md)** — Design patterns and philosophy
- **[Roadmap](../ROADMAP.md)** — Planned features
