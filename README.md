# 🌌 SocialSeed Tasker
## The Operational Brain for AI-Driven Engineering

**SocialSeed Tasker** is the definitive framework for teams and organizations scaling their development with AI Agents. While agents provide speed, Tasker provides the **Architectural Guardrails** that prevent your codebase from descending into chaos.

[![Version](https://img.shields.io/badge/Version-1.0.0-6366F1.svg?style=for-the-badge)](https://daironpf.github.io/socialseed-tasker/)
[![Architecture](https://img.shields.io/badge/Architecture-Hexagonal-A855F7.svg?style=for-the-badge)](https://daironpf.github.io/socialseed-tasker/pages/hexagonal.html)
[![Storage](https://img.shields.io/badge/Storage-Neo4j%20Graph-orange.svg?style=for-the-badge)](https://daironpf.github.io/socialseed-tasker/pages/graph-schema.html)

---

### 🚀 Why SocialSeed Tasker?

In the age of autonomous coding, speed is no longer the bottleneck—**context and safety are.** Tasker turns your repository into a living, reasoning graph that AI agents can navigate with precision, ensuring every change is calculated, documented, and safe.

#### 🛡️ Develop with Agents, Without the Breakage
Agents can't see what they might break three layers deep. Tasker can. Our **Graph-Based Impact Analysis** maps every dependency, blocking risky changes before they happen.

#### 🧠 Infinite Context for LLMs
Stop feeding agents raw text. Tasker's **Code-as-Graph** (powered by Tree-Sitter) provides agents with a semantic map of your functions, classes, and imports, reducing "hallucinations" and increasing success rates.

#### 👁️ Human-in-the-Loop Visibility
With **AI Reasoning Logs**, you see exactly *why* an agent made a decision. No more black boxes—just clear, traceable engineering logic.

---

### 💎 Key Features for the Modern Tech Stack

*   **Graph-Native Management**: Powered by **Neo4j**, managing complex microservices dependencies is as simple as a single query.
*   **Impact Analysis Engine**: Instantly calculate the "Blast Radius" of any code change or issue resolution.
*   **RAG-Powered Discovery**: Semantic search across your entire task history and codebase to find similar solutions in seconds.
*   **Architectural Constraints**: Set "Hard Rules" (e.g., "No circular dependencies", "Must use PostgreSQL") that both agents and humans must follow.
*   **Vue-Powered Observability**: A stunning Kanban and Graph dashboard to visualize your project's health in real-time.

---

### 🤖 Quick Start for AI Agents

Getting your agents up and running with Tasker takes seconds.

```bash
# 1. Install the Brain
pip install socialseed-tasker

# 2. Spin up the Infrastructure
docker compose up -d

# 3. Give the Agent Context (The Magic Part)
tasker agent context --issue "ISSUE_ID"
```

*This single command provides an agent with the specific code symbols, dependencies, and historical context needed to solve the task safely.*

---

### 🏢 Built for Scale

Whether you are a solo developer managing a dozen agents or an enterprise architect overseeing 50 microservices, Tasker scales with you.

*   **CTOs & Tech Leads**: Enforce architectural standards automatically across all teams.
*   **DevOps**: Monitor system stability and root-cause failures through causal graph inference.
*   **Product Managers**: Get real-time, data-driven insights into project blockers and critical paths.

---

### 📚 Full Documentation

For detailed technical guides, API references, and architectural deep-dives, visit our official documentation site:

👉 **[https://daironpf.github.io/socialseed-tasker/](https://daironpf.github.io/socialseed-tasker/)**

### 📖 v1.0.0 Documentation

- [Developer Onboarding Guide](docs/ONBOARDING.md) - Start here for new developers!
- [CLI Commands Reference](docs/CLI_COMMANDS.md)
- [API Reference](docs/API_REFERENCE.md)
- [Graph Model Schema](docs/GRAPH_MODEL.md)
- [RAG & Vector Indexes Guide](docs/RAG_GUIDE.md)
- [Code-as-Graph Guide](docs/CODE_GRAPH_GUIDE.md)

---

### 🔧 Troubleshooting

#### Neo4j Container Fails to Start

If you see the error: `Invalid value for password. It cannot be 'neo4j', which is the default.`

**Cause:** Neo4j 5.x security policy prevents using "neo4j" as the password (it must differ from the username).

**Solution:** Use a different password in `docker-compose.yml`:

```yaml
environment:
  - NEO4J_AUTH=neo4j/neoSocial  # password must NOT be "neo4j"
```

Also ensure the API environment variables match:
```yaml
- TASKER_NEO4J_PASSWORD=neoSocial
```

**Restart after changing:**
```bash
docker compose down -v
docker compose up -d
```

---

### 🤝 Contributing

We are building the future of autonomous engineering. Join us!
- **GitHub**: [daironpf/socialseed-tasker](https://github.com/daironpf/socialseed-tasker)
- **License**: Apache 2.0

---
<p align="center">
  <i>"Speed is a byproduct of clarity. Tasker provides the clarity."</i>
</p>