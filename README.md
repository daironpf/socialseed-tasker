# SocialSeed Tasker

**A graph-based task management framework designed for AI agents to manage issues with infinite context and architectural governance.**

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+">
  <img src="https://img.shields.io/badge/Architecture-Hexagonal-green.svg" alt="Hexagonal Architecture">
  <img src="https://img.shields.io/badge/Storage-Neo4j-orange.svg" alt="Neo4j">
</p>

---

## 🎯 Purpose: Built for AI Agents

SocialSeed Tasker is specifically designed to give **AI agents** superhuman capabilities in issue management:

- **Infinite Context**: AI agents can trace dependencies across thousands of issues instantly using graph traversal
- **Architectural Governance**: Automatically enforce component boundaries and forbidden dependencies
- **Root Cause Analysis**: Link failed tests to recent code changes using causal traceability
- **Autonomous Decision Making**: AI agents can query the dependency graph to understand what can be worked on and what is blocked

Traditional issue trackers treat issues as isolated items. SocialSeed Tasker treats them as a **knowledge graph** where relationships are first-class citizens—exactly what AI agents need to make intelligent decisions.

---

## 🚀 Quick Start for AI Agents

### AI agents can interact with Tasker through multiple interfaces:

```python
# Method 1: Direct Python API (recommended for AI agents)
from socialseed_tasker.core.task_management.actions import create_issue_action
from socialseed_tasker.core.task_management.entities import Component

# Create component and issues
component = Component(name="auth-service", project="my-project")
issue = create_issue_action(repo, title="Fix login bug", component_id=str(component.id))

# Query the dependency graph
chain = get_dependency_chain_action(repo, issue_id)
blocked = get_blocked_issues_action(repo)
```

```bash
# Method 2: CLI commands
tasker issue create "Implement OAuth2" --component <id> --priority HIGH
tasker dependency add <issue-id> <depends-on-id>
tasker dependency chain <issue-id>
```

```python
# Method 3: REST API for external AI systems
import requests
response = requests.post("http://localhost:8000/api/v1/issues/", json={
    "title": "Add caching layer",
    "component_id": "<component-uuid>",
    "priority": "HIGH",
    "labels": ["performance", "backend"]
})
```

---

## 🔑 Key Features for AI Agents

### 🔗 Intelligent Dependency Management

AI agents can understand complex dependency chains instantly:

```python
# Get full transitive dependency chain
chain = get_dependency_chain_action(repo, issue_id)
# Returns all issues that this issue depends on, recursively

# Find all blocked issues (issues waiting on open dependencies)
blocked = get_blocked_issues_action(repo)
# AI agent can immediately see what can be worked on
```

### 🏗️ Architectural Integrity Enforcement

AI agents automatically respect component boundaries:

```python
# Attempting to create a forbidden dependency is automatically rejected
add_dependency_action(repo, frontend_issue_id, database_issue_id)
# Raises: ForbiddenDependencyError: Frontend cannot depend on Database
```

### 🔍 Root Cause Analysis

Link test failures to recent issues for autonomous debugging:

```python
from socialseed_tasker.core.project_analysis.analyzer import RootCauseAnalyzer

analyzer = RootCauseAnalyzer(repo)
causal_links = analyzer.find_root_cause(test_failure, closed_issues)
# Returns ranked list of likely root causes with confidence scores
```

### 🌐 Project Structure Detection

Automatically detect real project modules (microservices, packages, Python modules):

```bash
# Detect project structure
tasker project detect --path /path/to/project

# Setup components for all detected modules
tasker project setup --path /path/to/project --project "my-project"
```

---

## 📋 Usage Examples

### Creating Issues with Dependencies

```bash
# Create components for different services
tasker component create auth-service --project "social-network"
tasker component create user-service --project "social-network"

# Create issues
tasker issue create "Implement JWT refresh" --component <auth-id> --priority HIGH
tasker issue create "Add user profile API" --component <user-id> --priority MEDIUM

# Make user service depend on auth (AI agent knows the order now!)
tasker dependency add <user-issue-id> <auth-issue-id>
```

### Querying What Can Be Worked On

```bash
# AI agent: "What issues can I work on right now?"
tasker dependency blocked
# Returns: All issues that are NOT blocked (their dependencies are closed)

# AI agent: "What's the full impact of this change?"
tasker analyze impact <issue-id>
# Returns: Directly and transitively affected issues
```

---

## 🛠️ Installation

### From PyPI (Recommended)

```bash
# Install the latest version
pip install socialseed-tasker

# With Neo4j support (optional)
pip install socialseed-tasker[neo4j]

# With all dependencies
pip install socialseed-tasker[dev]
```

### From Source

```bash
# Clone and install
git clone https://github.com/daironpf/socialseed-tasker.git
cd socialseed-tasker
pip install -e ".[dev]"

# Start Neo4j
docker compose up -d

# Verify installation
tasker --help

---

## 💾 Storage Backends

| Backend | Use Case | Command |
|---------|----------|---------|
| **Neo4j** (default) | Production with full graph capabilities | `--backend neo4j` |
| **File** | Development/testing | `--backend file` |

### Neo4j Configuration

```bash
# Local Docker (default ports: 17689 for Bolt, 18082 for HTTP)
--neo4j-uri bolt://localhost:17689
--neo4j-password <password>

# Neo4j Aura (cloud)
--neo4j-uri bolt+s://your-aura-id.databases.neo4j.io:7687
--neo4j-password <aura-password>
```

---

## 🤖 AI Agent Integration

### Injected Skills System

Tasker can be injected into any external project, giving AI agents immediate access to issue management:

```bash
# In your target project
tasker init

# This creates:
# project/
# └── tasker/
#     ├── skills/           # Python modules AI agents can import
#     │   ├── task_skill.py # Function calling bridge
#     │   └── skill_manifest.json
#     ├── configs/
#     └── docker-compose.yml
```

AI agents can then import and use the skills directly:

```python
import sys
sys.path.insert(0, "tasker/skills")
from task_skill import create_issue, list_issues, add_dependency

# Create issues (AI agent can do this autonomously!)
result = create_issue(
    title="Refactor authentication",
    component_id="<uuid>",
    priority="HIGH"
)

# AI agent can check what depends on what
issues = list_issues(component_id="<uuid>")
```

---

## 📊 Architecture

```
                    ┌─────────────────────┐
                    │   AI Agent / CLI    │
                    │   REST API          │
                    └─────────┬───────────┘
                              ▼
              ┌─────────────────────────────┐
              │      Application Core      │
              │  • Issue Management         │
              │  • Dependency Graph        │
              │  • Architectural Rules      │
              │  • Root Cause Analysis     │
              └─────────────┬───────────────┘
                            ▼
    ┌──────────────────────────┐   ┌──────────────────────────┐
    │   Neo4j (Graph Storage)  │   │   File (JSON Fallback)   │
    │   • Full graph queries   │   │   • Simple storage       │
    │   • Cypher traversal     │   │   • Development use      │
    └──────────────────────────┘   └──────────────────────────┘
```

---

## 🎓 Why Graph-Based for AI Agents?

### Traditional Issue Trackers
- Issues are isolated rows in a database
- AI agent must scan thousands of records to understand relationships
- No way to ask "what depends on this?"

### SocialSeed Tasker
- Issues are nodes in a knowledge graph
- AI agent can traverse relationships instantly: `MATCH (i:Issue {id:'x'})-[:DEPENDS_ON*]->(d)`
- Natural language queries become graph queries
- AI can reason about **what's possible** vs **what's blocked**

---

## 📖 Detailed Documentation

- **[CLI Reference](#)** - All available commands
- **[API Documentation](#)** - REST API endpoints
- **[Hexagonal Architecture](#)** - Code organization principles
- **[Configuration](#)** - Environment variables and settings
- **[Development Guide](#)** - Running tests, linting, contributing

---

## 🔧 Commands Reference

| Command | Description |
|---------|-------------|
| `tasker init` | Initialize Tasker in external project |
| `tasker status` | Show current configuration |
| `tasker component create` | Create a component |
| `tasker component list` | List all components |
| `tasker issue create` | Create an issue |
| `tasker issue list` | List issues (with filters) |
| `tasker issue show` | Show issue details |
| `tasker dependency add` | Add dependency between issues |
| `tasker dependency chain` | Show dependency chain |
| `tasker dependency blocked` | Show unblocked issues |
| `tasker project detect` | Detect project modules |
| `tasker project setup` | Create components from modules |
| `tasker analyze root-cause` | Find root causes for test failures |
| `tasker analyze impact` | Analyze issue impact |

---

## 🤝 Contributing

Built as part of the [SocialSeed Project](https://github.com/daironpf/SocialSeed). Licensed under Apache 2.0.

---

## 📂 Project Structure

```
socialseed-tasker/
├── src/socialseed_tasker/
│   ├── core/                    # Pure business logic (no dependencies)
│   │   ├── task_management/     # Issue and component management
│   │   └── project_analysis/    # Root cause and impact analysis
│   ├── entrypoints/             # Interfaces (CLI, API, init)
│   ├── storage/                 # Neo4j and file adapters
│   ├── bootstrap/               # Dependency injection
│   └── assets/                  # Templates for injected setup
├── .agent/                      # AI agent documentation
│   ├── skills/                  # Agent capabilities
│   └── workflows/               # Step-by-step procedures
├── tests/                       # Test suite
└── docker-compose.yml           # Neo4j for local development
```