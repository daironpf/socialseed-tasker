# SocialSeed Tasker 🛡️🌱

**SocialSeed Tasker** is an AI-native task management framework designed to bridge the gap between autonomous AI agents and architectural integrity. By leveraging **Neo4j** as a knowledge graph, it transforms static "to-do lists" into a dynamic map of engineering decisions.

Part of the [SocialSeed Project](https://github.com/daironpf/SocialSeed).

## 🚀 Key Features

- **Graph-First Architecture:** Relationships like `DEPENDS_ON`, `BLOCKS`, and `AFFECTS` are treated as first-class citizens.
- **AI-Native Skills:** Built-in hooks for AI agents to create, analyze, and resolve issues without breaking project ergonomics.
- **Docker-Ready:** Seamless integration with Neo4j Community Edition via Docker Compose.
- **E2E Integration:** Designed to work alongside `socialseed-e2e` for automated bug reporting.

## 🛠️ Tech Stack

- **Language:** Python 3.10+
- **Database:** Neo4j (Graph Database)
- **Containerization:** Docker & Docker Compose
- **CLI Framework:** Typer
- **Validation:** Pydantic v2

## 📦 Installation (Coming Soon to PyPI)

```bash
pip install socialseed-tasker
