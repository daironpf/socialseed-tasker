# 🤝 Contributing to SocialSeed Tasker

First of all, thank you for considering contributing to **SocialSeed Tasker**! It’s community involvement like yours that makes open-source projects thrive.

As a **Graph-Native** and **Architecturally Governed** project, we have specific standards to ensure the codebase remains clean, maintainable, and scalable.

---

## 🏗️ Architectural Principles

Before you write a single line of code, please keep our **Hexagonal Architecture** in mind:

1.  **Domain is King:** The core logic (Entities and Actions) must have **zero dependencies** on external frameworks or databases (No FastAPI, no Neo4j drivers here).
2.  **Infrastructure is a Detail:** Database implementations (Neo4j), CLI (Rich), and API (FastAPI) live in the `infrastructure` or `entrypoints` layers. They "serve" the domain.
3.  **Dependency Rule:** Dependencies only point **inwards**. Infrastructure knows about the Domain, but the Domain never knows about Infrastructure.

---

## 🚀 How Can I Contribute?

### 1. Reporting Bugs
* Check the **Issues** tab to see if the bug has already been reported.
* If not, open a new issue using a clear title and a detailed description (including steps to reproduce).

### 2. Suggesting Enhancements
* We love new ideas! Please open an issue first to discuss the feature before starting to code. This ensures the suggestion aligns with the project’s roadmap.

### 3. Pull Requests (PRs)
1.  **Fork** the repository.
2.  **Create a branch** for your feature or fix: `git checkout -b feature/your-feature-name` or `git checkout -b fix/issue-id`.
3.  **Follow the Style:** We use standard Python PEP 8. Please ensure your code is readable.
4.  **Write Tests:** We have a high standard for stability. If you add a feature, add a unit test in the `tests/` directory.
5.  **Submit the PR:** Provide a clear description of what you changed and why.

---

## 🛠️ Development Setup

Since this is a **Neo4j-Exclusive** project, you will need a running instance of Neo4j to test your changes:

```bash
# 1. Clone your fork
git clone https://github.com/YOUR-USERNAME/socialseed-tasker.git

# 2. Setup environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# 3. Spin up Neo4j via Docker (service is named tasker-db)
docker compose up -d tasker-db

# 4. Run tests to ensure everything is green
pytest