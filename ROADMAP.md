# 🗺️ SocialSeed Tasker: Strategic Roadmap

SocialSeed Tasker is an **AI-Native Project Management Framework** powered by **Neo4j**. Our mission is to move beyond flat task lists and into **Graph-Based Architectural Governance** for autonomous software engineering.

This roadmap outlines our journey from a core utility to a global standard for AI-driven development.

**Last updated:** 2026-04-12 (v0.8.0 - Issues #136-140 resolved)

---

## 📍 Phase 1: Foundation & Injected Infrastructure (Q2 2026)
*Goal: Make Tasker the easiest "Sidecar" to install and configure.*

* [x] **Core Hexagonal Architecture:** Implementation of Feature-Oriented layers (API, Domain, Infrastructure).
* [x] **Injected Scaffolding (`tasker init`):** CLI command to "seed" existing projects with AI Skills and Docker configurations. Supports `--force` flag for overwriting.
* [x] **Hybrid Persistence:** Seamless toggle between **Local Neo4j (Docker)** and **Neo4j Aura DB (Cloud)** via environment profiles. Auto-detection of encryption from URI.
* [x] **Asset Templates:** Standardized Python/JSON "Skill" templates for external AI Agent integration.
* [x] **CLI - Component Management:** `create`, `list`, `show`, `update`, `delete` with Rich output.
* [x] **CLI - Component Name Lookup:** `show`, `update`, `delete` support name, partial ID (8+ chars), or full UUID.
* [x] **CLI - Issue Management:** `create`, `list`, `show`, `close` with validation (blocks open dependencies).
* [x] **CLI - Issue Title Lookup:** Dependency commands (`add`, `remove`, `list`, `chain`) support issue titles of any length.
* [x] **CLI - Dependency Management:** `add`, `list`, `chain`, `blocked` with circular dependency detection (BFS).
* [x] **CLI - Analysis:** `root-cause` (graph proximity + temporal + semantic scoring) and `impact` (BFS transitive analysis with risk levels).
* [x] **CLI - Project Detection:** `project detect` and `project setup` for auto-discovering modules from docker-compose, src/, etc.
* [x] **CLI - Status:** `status` command showing current backend configuration.
* [x] **REST API (FastAPI):** Full CRUD for issues, components, dependencies. OpenAPI docs at `/docs`.
* [x] **REST API - Analysis Endpoints:** `POST /analyze/root-cause` and `GET /analyze/impact/{id}` with typed schemas.
* [x] **REST API - Consistent Envelopes:** All responses use `{data, error, meta}` format with pagination support.
* [x] **Dependency Injection Container:** Environment-based configuration with wiring.
* [x] **Neo4j Storage Backend:** Graph database with Cypher queries, relationship management.
* [x] **Docker Compose Setup:** API + Frontend + Neo4j (tasker-db) services.
* [x] **Entry Points:** Both `tasker` and `socialseed-tasker` CLI commands available.
* [x] **REST API Health Endpoint:** `/health` for container health checks.

---

## 🧠 Phase 2: Graph Intelligence & Observability (Q3 2026)
*Goal: Provide a "God-View" for humans and a "Reasoning Brain" for AI.*

* [x] **Causal Traceability:** Root cause analysis links test failures to closed issues via component match, temporal recency, label overlap, semantic similarity, and graph proximity (BFS bidirectional).
* [x] **The Human-Centric Board:** Vue.js Kanban board with drag & drop, auto-refresh (10s), responsive columns, and real-time agent activity indicator.
* [ ] **AI Reasoning Logs:** In-issue Markdown summaries explaining *why* the AI chose a specific architectural path based on the graph.
* [ ] **Live Agent Documentation:** Agents must maintain a "Dynamic Progress Manifest" within the issue description, including:
    * **Live TODO List:** Checkboxes updated as the agent completes sub-tasks.
    * **Affected Files:** Real-time list of created or modified files.
    * **Technical Debt Notes:** Observations made by the agent during implementation.
* [x] **Advanced Cypher Queries:** Impact analysis with BFS for direct/transitive dependents, blocked issues detection, affected components collection, and risk level calculation (LOW/MEDIUM/HIGH/CRITICAL).
* [x] **Architectural Analysis Module:** Rule-based analyzer for forbidden technologies, required patterns, forbidden dependencies, and max dependency depth validation.
* [x] **Graph Visualization:** Interactive graph view of issues, components, and dependencies (beyond Kanban) integrated directly into the UI dashboard.
* [ ] **Issue `agent_working` Field:** Field exists in entity and API but needs full lifecycle integration (start/finish tracking).

---

## 🛡️ Phase 3: Architectural Governance (Q4 2026)
*Goal: Prevent AI from introducing technical debt or breaking system constraints.*

* **[ ] Cloud Sync & GitHub Integration:**
    * [ ] **GitHub API Adapter:** Implementation of a Hexagonal Adapter to map Tasker Issues to GitHub Issues/Milestones.
    * [ ] **Bidirectional Webhook Listener:** API endpoint to receive real-time updates from GitHub (comments, label changes, status updates).
    * [ ] **Causal Mirroring:** Automated sync of Tasker's "Analysis" (Root Cause/Impact) as comments in GitHub Issues for human reviewers.
    * [ ] **Offline-First Sync Engine:** Queue system to batch local changes and push them to GitHub once internet connection is restored (Critical for intermittent connectivity).
    * [ ] **Label-to-Graph Mapping:** Syncing GitHub Labels directly into Neo4j nodes for enhanced filtering
    * [ ] **`GitHubIssueMapper`:** Implement domain service to map Neo4j UUIDs to GitHub Issue numbers and metadata.    
    ### ☁️ GitHub Cloud Integration (High Priority)
    * [ ] **`ConnectivityManager` & `SyncQueue`:** Implement an offline-first "Guard" that queues agent actions during power/internet outages and flushes them to the cloud upon reconnection.
    * [ ] **`WebhookSignatureValidator`:** Secure endpoint for real-time bidirectional sync from GitHub.
    * [ ] **`MarkdownTransformer`:** Convert Graph Analysis results into GitHub-flavored Markdown (Tables and Mermaid diagrams).
    * [ ] **`SecretManager`:** Secure handling of GitHub Personal Access Tokens (PAT) via environment injection.
* [x] **Architectural Rule Engine:** Define rules for forbidden technologies, required patterns, forbidden dependencies, max depth. Violation reporting with errors/warnings. *(Note: exists in `core/project_analysis/` but not yet enforced at API/CLI level)*
* [ ] **Self-Documenting Enforcement:** Governance policy that blocks an agent from closing an issue if the "Solution Summary" and "Modified Files" sections are missing or incomplete.
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
| Unit Tests | ✅ 147 passed | Entities, actions, API, CLI, Neo4j repo, scaffolder, analyzers |
| Neo4j Integration | ✅ Working | All queries functional with graph storage |
| CLI Functional | ✅ All commands | Tested with mock repositories |
| API Functional | ✅ All endpoints | Tested via TestClient |
| E2E | ❌ Not implemented | No end-to-end test suite yet |

---

## 🔍 Known Issues (from audit)

| # | Issue | Severity | Location | Status |
|---|-------|----------|----------|--------|
| 1 | `issue show` requires full UUID, short ID fails | Low | CLI commands | ✅ RESOLVED (v0.5.0) |
| 2 | `component show` requires full UUID, short ID fails | Low | CLI commands | ✅ RESOLVED (v0.8.0 #134) |
| 3 | `POST /dependencies` route not mounted at `/api/v1/dependencies` | Medium | Route prefix mismatch | ✅ RESOLVED |
| 4 | `POST /analyze/root-cause` requires `test_id` field not documented in CLI help | Low | Schema vs CLI mismatch | ✅ RESOLVED (v0.5.1) - Added /analyze/link-test |
| 5 | Architectural rules exist but not enforced at API/CLI write level | Medium | Integration gap | ⚠️ OPEN |
| 6 | No filtering by project in issue list | Low | API & CLI | ✅ RESOLVED (v0.5.0) |
| 7 | Dependencies not populated in issue list response | Low | API | ✅ RESOLVED (v0.5.0) |
| 8 | No bulk dependency creation | Low | API | ✅ RESOLVED (v0.5.0) |
| 9 | CLI output has extra blank lines at start (Typer/Rich bug) | Low | CLI rendering | ⚠️ LIMITACIÓN CONOCIDA - No hay solución sin cambiar de framework CLI |
| 10 | `component update` requires full UUID | Low | CLI commands | ✅ RESOLVED (v0.8.0 #136) |
| 11 | `dependency add` requires full UUID for issue titles | Low | CLI commands | ✅ RESOLVED (v0.8.0 #137) |
| 12 | `component delete` requires full UUID | Low | CLI commands | ✅ RESOLVED (v0.8.0 #138) |
| 13 | `/analyze/component-impact` API requires full UUID | Low | API routes | ✅ RESOLVED (v0.8.0 #139) |
| 14 | `test_component_show_missing` expects wrong exit code | Low | Test | ✅ RESOLVED (v0.8.0 #140) |
| 15 | Linter F821 - undefined UUID and Any | Low | Code | ✅ RESOLVED (v0.8.0 #141) |
| 16 | Linter F401 - unused imports | Low | Code | ✅ RESOLVED (v0.8.0 #142) |
| 17 | Linter F541, B904 - code quality | Low | Code | ✅ RESOLVED (v0.8.0 #143) |
| 18 | Linter I001, E501 - formatting | Low | Code | ✅ RESOLVED (v0.8.0 #144) |
| 19 | Docker frontend build failure | Medium | Docker | ✅ RESOLVED (v0.8.0 #145) |

---

## 📋 Limitaciones Conocidas

### CLI Blank Lines Issue
La salida del CLI (`tasker --help`, `tasker issue list`, etc.) muestra líneas en blanco adicionales al inicio de cada comando. Este es un problema conocido a nivel de la integración Typer + Rich que no tiene solución directa sin migrar a otro framework CLI (como Click o argparse básico).

**Estado:** No resuelto - Limitación conocida
**Impacto:** Bajo - Solo afecta la presentación visual
**Workaround:** Ninguno disponible actualmente

---

**Building the future of software engineering, one node at a time.** 🛡️🕸️

---