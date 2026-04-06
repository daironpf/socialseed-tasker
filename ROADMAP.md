# 🗺️ SocialSeed Tasker: Strategic Roadmap

SocialSeed Tasker is an **AI-Native Project Management Framework** powered by **Neo4j**. Our mission is to move beyond flat task lists and into **Graph-Based Architectural Governance** for autonomous software engineering.

This roadmap outlines our journey from a core utility to a global standard for AI-driven development.

**Last updated:** 2026-04-06 (Full functional audit)

---

## 📍 Phase 1: Foundation & Injected Infrastructure (Q2 2026)
*Goal: Make Tasker the easiest "Sidecar" to install and configure.*

* [x] **Core Hexagonal Architecture:** Implementation of Feature-Oriented layers (API, Domain, Infrastructure).
* [x] **Injected Scaffolding (`tasker init`):** CLI command to "seed" existing projects with AI Skills and Docker configurations. Supports `--force` flag for overwriting.
* [x] **Hybrid Persistence:** Seamless toggle between **Local Neo4j (Docker)** and **Neo4j Aura DB (Cloud)** via environment profiles. Auto-detection of encryption from URI.
* [x] **Asset Templates:** Standardized Python/JSON "Skill" templates for external AI Agent integration.
* [x] **CLI - Component Management:** `create`, `list`, `show`, `update`, `delete` with Rich output.
* [x] **CLI - Issue Management:** `create`, `list`, `show`, `close` with validation (blocks open dependencies).
* [x] **CLI - Dependency Management:** `add`, `list`, `chain`, `blocked` with circular dependency detection (BFS).
* [x] **CLI - Analysis:** `root-cause` (graph proximity + temporal + semantic scoring) and `impact` (BFS transitive analysis with risk levels).
* [x] **CLI - Project Detection:** `project detect` and `project setup` for auto-discovering modules from docker-compose, src/, etc.
* [x] **CLI - Status:** `status` command showing current backend configuration.
* [x] **REST API (FastAPI):** Full CRUD for issues, components, dependencies. OpenAPI docs at `/docs`.
* [x] **REST API - Analysis Endpoints:** `POST /analyze/root-cause` and `GET /analyze/impact/{id}` with typed schemas.
* [x] **REST API - Consistent Envelopes:** All responses use `{data, error, meta}` format with pagination support.
* [x] **Dependency Injection Container:** Environment-based configuration with wiring.
* [x] **File Storage Backend:** JSON file persistence with atomic writes, backup/restore.
* [x] **Neo4j Storage Backend:** Graph database with Cypher queries, relationship management.
* [x] **Docker Compose Setup:** API + Frontend services with file-based storage volume.
* [x] **Entry Points:** Both `tasker` and `socialseed-tasker` CLI commands available.

---

## 🧠 Phase 2: Graph Intelligence & Observability (Q3 2026)
*Goal: Provide a "God-View" for humans and a "Reasoning Brain" for AI.*

* [x] **Causal Traceability:** Root cause analysis links test failures to closed issues via component match, temporal recency, label overlap, semantic similarity, and graph proximity (BFS bidirectional).
* [x] **The Human-Centric Board:** Vue.js Kanban board with drag & drop, auto-refresh (10s), responsive columns, and real-time agent activity indicator.
* [ ] **AI Reasoning Logs:** In-issue Markdown summaries explaining *why* the AI chose a specific architectural path based on the graph.
* [x] **Advanced Cypher Queries:** Impact analysis with BFS for direct/transitive dependents, blocked issues detection, affected components collection, and risk level calculation (LOW/MEDIUM/HIGH/CRITICAL).
* [x] **Architectural Analysis Module:** Rule-based analyzer for forbidden technologies, required patterns, forbidden dependencies, and max dependency depth validation.
* [ ] **Graph Visualization:** Interactive graph view of issues, components, and dependencies (beyond Kanban).
* [ ] **Issue `agent_working` Field:** Field exists in entity and API but needs full lifecycle integration (start/finish tracking).

---

## 🛡️ Phase 3: Architectural Governance (Q4 2026)
*Goal: Prevent AI from introducing technical debt or breaking system constraints.*

* [x] **Architectural Rule Engine:** Define rules for forbidden technologies, required patterns, forbidden dependencies, max depth. Violation reporting with errors/warnings. *(Note: exists in `core/project_analysis/` but not yet enforced at API/CLI level)*
* [ ] **Graph Policy Engine:** Define "Rules of the Graph" (e.g., *Layer A cannot touch Layer C*) enforced at write time.
* [ ] **Pre-Execution Validation:** Tasker automatically blocks agent actions that violate defined architectural policies.
* [ ] **Automated Self-Healing:** Integration with `socialseed-e2e` to trigger "Fix Issues" automatically when tests fail.
* [ ] **Swarm Coordination:** Multi-agent role management (Planner, Developer, Reviewer) synchronized via Graph states.
* [ ] **Transaction Boundaries:** Atomic multi-operation commits to prevent race conditions (currently no transaction support in file backend).

---

## 🚀 Phase 4: Global Ecosystem & Autonomous Execution (2027)
*Goal: Full autonomy and industry-wide adoption.*

* [ ] **IDE Integration (Plugins):** Native extensions for **Cursor, VS Code, and Windsurf** to interact with the Tasker API.
* [ ] **Autonomous Git Operations:** Full lifecycle management from Issue creation to PR merging with graph-verified approvals.
* [ ] **Project "Master Config" (YAML-to-Graph):** A single file that defines the entire system architecture, which Tasker then enforces.
* [ ] **Community Demos:** Production-ready boilerplate examples (E-commerce, SaaS API) managed entirely by SocialSeed Tasker.

---

## 📊 Test Coverage

| Area | Status | Notes |
|------|--------|-------|
| Unit Tests | ✅ 178 passed | Entities, actions, API, CLI, file repo, scaffolder, analyzers |
| Neo4j Integration | ⚠️ 11 errors | Requires Docker/Neo4j running |
| CLI Functional | ✅ All commands | Tested in isolated environment |
| API Functional | ✅ All endpoints | Tested via TestClient |
| E2E | ❌ Not implemented | No end-to-end test suite yet |

---

## 🔍 Known Issues (from audit)

| # | Issue | Severity | Location |
|---|-------|----------|----------|
| 1 | `issue show` requires full UUID, short ID fails | Low | CLI commands |
| 2 | `component show` requires full UUID, short ID fails | Low | CLI commands |
| 3 | API root `/` returns 404 (no health endpoint) | Low | `app.py` |
| 4 | `POST /dependencies` route not mounted at `/api/v1/dependencies` | Medium | Route prefix mismatch |
| 5 | `POST /analyze/root-cause` requires `test_id` field not documented in CLI help | Low | Schema vs CLI mismatch |
| 6 | No transaction support in file backend (race condition risk) | High | `FileTaskRepository` |
| 7 | Architectural rules exist but not enforced at API/CLI write level | Medium | Integration gap |

---

**Building the future of software engineering, one node at a time.** 🛡️🕸️

---
