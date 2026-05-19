# CLI Commands Reference - v1.0.0

This document covers all CLI commands available in SocialSeed Tasker v1.0.0.

## Installation

```bash
pip install socialseed-tasker
tasker --help
```

## Issue Management

### Create Issue
```bash
tasker issue create --title "Fix login bug" --component backend --priority HIGH
```

### List Issues
```bash
tasker issue list --status OPEN --project myproject
```

### Show Issue Details
```bash
tasker issue show <issue-id>
```

### Close Issue
```bash
tasker issue close <issue-id>
tasker issue close <issue-id> --affects <file-path> --affects <file-path>
```

### Delete Issue
```bash
tasker issue delete <issue-id>
```

### Move Issue
```bash
tasker issue move <issue-id> --to-component <component-id>
```

### Start Working on Issue
```bash
tasker issue start <issue-id>
```

### Finish Working on Issue
```bash
tasker issue finish <issue-id>
```

## Component Management

### Create Component
```bash
tasker component create --name api-gateway --project myproject
```

### List Components
```bash
tasker component list --project myproject
```

### Show Component
```bash
tasker component show <component-id>
```

### Update Component
```bash
tasker component update <component-id> --name <new-name>
```

### Delete Component
```bash
tasker component delete <component-id>
```

### Add Component Dependency
```bash
tasker component add-dependency <component-id> --depends-on <dep-id>
```

### List Component Dependencies
```bash
tasker component list-dependencies <component-id>
```

## Dependency Management

### Add Dependency
```bash
tasker dependency add <issue-id> --depends-on <dep-id>
```

### Remove Dependency
```bash
tasker dependency remove <issue-id> <depends-on-id>
```

### List Dependencies
```bash
tasker dependency list <issue-id>
```

### Dependency Chain
```bash
tasker dependency chain <issue-id>
```

### Blocked Issues
```bash
tasker dependency blocked
```

## Analysis Commands

### Impact Analysis
```bash
tasker analyze impact <issue-id>
```

### Code Impact Analysis
```bash
tasker analyze code-impact <file-path>
```

### Root Cause Analysis
```bash
tasker analyze root-cause <issue-id>
```

### Phantom Dependency Detection (v1.0.0)
```bash
tasker analyze similarity --issue <issue-id>
tasker analyze similarity --issue <issue-id> --threshold 0.7 --limit 10
```

### ARCHITECT Agent (v1.0.0)
```bash
tasker agent architect --issue <issue-id>
tasker agent architect --issue <issue-id> --check
```

### Agent Integration

## Code Graph (v1.0.0)

### Scan Code Repository
```bash
tasker code-graph scan /path/to/repo
```

### Find Code Symbols
```bash
# Find by name
tasker code-graph find --name "function_name"

# Find by type
tasker code-graph find --type class --name "UserService"

# Find by language
tasker code-graph find --language python --name "handler"
```

### List Code Files
```bash
tasker code-graph files
```

### Code Graph Stats
```bash
tasker code-graph stats
```

### Clear Code Graph
```bash
tasker code-graph clear
```

### Impact Analysis (Code Level)
```bash
tasker code-graph impact <symbol-id>
```

### Find Function Callers
```bash
tasker code-graph calls <symbol-id>
```

### Find Dependencies
```bash
tasker code-graph depends <symbol-id>
```

### Find Tests
```bash
tasker code-graph tests <symbol-id>
```

### Get File Details
```bash
tasker code-graph file <file-path>
```

## RAG Commands (v1.0.0)

### Semantic Search
```bash
tasker rag search "how to implement authentication"
```

### Index Content
```bash
tasker rag index --source issue --id <issue-id>
```

### RAG Stats
```bash
tasker rag stats
```

### Clear RAG Index
```bash
tasker rag clear --yes
```

## Agent Commands (v1.0.0)

### Get Agent Context
```bash
tasker agent context --issue <issue-id>
```

### Get Suggestions
```bash
tasker agent suggest --issue <issue-id>
```

### View Agent Reasoning
```bash
tasker agent reasoning --issue <issue-id>
```

## Agent Registration Commands (v1.0.0)

### Register Agent
Register a new agent with Tasker for tracking and specialization.
```bash
tasker agent register --id <agent-id> --name <name> --role <role> --capabilities <cap1,cap2>
```

Assign agent to project on registration:
```bash
tasker agent register --id <agent-id> --name <name> --role <role> --capabilities <cap1,cap2> --project-id <project-id>
```

| Flag | Description |
|------|-------------|
| `--id, -i` | Unique agent identifier (e.g., "agent-001") |
| `--name, -n` | Human-readable agent name |
| `--role, -r` | Agent role: developer, reviewer, planner, observer, tester, architect |
| `--capabilities, -c` | Comma-separated capabilities (e.g., "coding,testing") |
| `--project-id, -p` | Optional project ID to assign the agent to (auto-links if only one project exists) |

### Add Agent Specialization
Assign an agent to specialize in a specific component for domain-driven dispatching.
```bash
tasker agent specialize --agent <agent-id> --component <component-id>
```

| Flag | Description |
|------|-------------|
| `--agent, -a` | Agent ID |
| `--component, -c` | Component ID to specialize in |

### List Agents
```bash
tasker agent list
```

## Reasoning Commands (v1.0.0)

### Log Reasoning
```bash
tasker reasoning log --issue <issue-id> --thought "Choosing solution A because..."
```

### View Reasoning History
```bash
tasker reasoning history --issue <issue-id>
```

### Reasoning Stats
```bash
tasker reasoning stats
```

### Clear Reasoning Logs
```bash
tasker reasoning clear
```

## Constraints

### Set Constraint
```bash
tasker constraints set --name no-circular-deps --rule "no_circular_dependencies"
```

### List Constraints
```bash
tasker constraints list
```

### Validate Constraints
```bash
tasker constraints validate
```

## Storage

### Run Migrations
```bash
tasker storage migrate --version 0.9.0
```

### Rollback Migration
```bash
tasker storage rollback --version 0.9.0
```

## Authentication

### Login
```bash
tasker login --uri bolt://localhost:7687 --user neo4j
```

### Logout
```bash
tasker logout
```

## Project Commands

### Detect Project
```bash
tasker project detect --path /path/to/project
```

### Setup Project
```bash
tasker project setup --path /path/to/project
```

## Seed Data

### Run Seed
```bash
tasker seed run
```

## Server Management (v1.0.1+)

### Start API Server
```bash
# Start server on default port (8000)
tasker serve

# Start on custom port
tasker serve --port 9000

# Start with auto-reload (development)
tasker serve --reload
```

### Restart Docker Services
```bash
# Build and restart all Docker containers
tasker restart

# Start without rebuilding
tasker restart --build false

# Force rebuild (--no-cache)
tasker restart --force
```

### Docker Compose (Alternative)
```bash
# Start Neo4j only
cd .agent && docker compose up -d tasker-db

# Start all services
cd .agent && docker compose up -d

# Rebuild before starting
cd .agent && docker compose build --no-cache && docker compose up -d
```