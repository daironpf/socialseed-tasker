# Release Versioning Strategy - SocialSeed Tasker

This document defines the versioning milestones for **SocialSeed Tasker**. We strictly follow [Semantic Versioning (SemVer)](https://semver.org/), ensuring that every release communicates its level of stability and functional scope to both human developers and AI agents.

---

## Versioning Policy Note

**Major Version Zero (0.y.z):** Per SemVer standards, while the project is in the `0.y.z` phase, the API and core structures are considered unstable. 
* **The "Strict Major" rule:** Enforcement of MAJOR version increments for breaking changes will officially begin **only after the release of version 1.0.0**. 
* Until then, breaking changes may occur in MINOR releases (`0.x.0`) to allow for rapid architectural evolution.

---

## Current Milestone: v0.8.0 (The "Observability & Active Governance" Release)

**Status:** *Released* on 2026-04-23

SocialSeed Tasker is a **Graph-Only** platform, leveraging Neo4j as its exclusive source of truth.

* **Focus:** Human-in-the-loop transparency and enforcement.
* **Audit Status:** 270+ unit tests passing.
* **Key Goal:** GitHub integration, policy enforcement, and AI agent observability.

---

## v0.8.0 Complete Feature Checklist

### Core Infrastructure (v0.x base)

- [x] **Neo4j as Exclusive Storage:** File storage removed, only Neo4j backend supported.
- [x] **Graph Traversal (BFS):** Dependency chain analysis, circular dependency detection, blocked issues.
- [x] **Human-Centric UI:** Vue.js Kanban board with drag & drop, auto-refresh, agent_working indicator.
- [x] **REST API for AI Agents:** Full CRUD for issues, components, dependencies with consistent error envelopes.
- [x] **CLI Interface:** Typer + Rich CLI with issue, component, dependency, and analysis commands.
- [x] **Root Cause Analysis:** Scoring system with component match, temporal recency, label overlap, semantic similarity, graph proximity.
- [x] **Impact Analysis:** BFS for direct/transitive dependents, blocked issues detection, risk levels (LOW/MEDIUM/HIGH/CRITICAL).
- [x] **Docker Compose:** Three services (Neo4j, API, Frontend) with health checks and networking.
- [x] **Project Scaffolding:** `tasker init` command to inject Tasker infrastructure into external projects.
- [x] **Neo4j Aura DB Support:** Auto-detection of encryption mode from URI (bolt+s://, neo4j+s://).
- [x] **Agent Working Indicator:** `agent_working` field with UI indicator (cyan robot icon).
- [x] **AI Agent Workflow:** REST API with OpenAPI docs, consistent JSON envelopes, progress tracking via issue descriptions.
- [x] **Advanced Cypher Queries:** Impact analysis with BFS for direct/transitive dependents, blocked issues detection, affected components collection, and risk level calculation.
- [x] **Architectural Analysis Module:** Rule-based analyzer for forbidden technologies, required patterns, forbidden dependencies, and max dependency depth validation.
- [x] **Short ID Resolution:** Support for short UUID aliases in `show` and `update` commands.
- [x] **API Health Endpoint:** Implement `/health` with Neo4j connectivity status.
- [x] **Project Filter:** Add filtering by project name to issue list API and CLI.
- [x] **Demo Mode:** Auto-seed sample data on first startup with `TASKER_DEMO_MODE` env var.
- [x] **Bulk Dependencies:** API endpoint to create multiple dependencies in one request.
- [x] **Component Name Lookup:** Add name query parameter to GET /components endpoint.
- [x] **Optional Component:** Allow creating issues without component (uses 'uncategorized' default).
- [x] **Duplicate Detection:** Warn when creating issues with duplicate titles in same component.

---

### v0.8.0 GitHub Integration

- [x] **#88 GitHub API Adapter:** Hexagonal Adapter to map Tasker Issues to GitHub Issues/Milestones.
- [x] **#89 Bidirectional Webhook Listener:** API endpoint to receive real-time updates from GitHub.
- [x] **#90 Causal Mirroring:** Automated sync of Tasker's Analysis as comments in GitHub Issues.
- [x] **#91 Offline-First Sync Engine:** Queue system to batch local changes and push when online.
- [x] **#92 Label-to-Graph Mapping:** Syncing GitHub Labels directly into Neo4j nodes.
- [x] **#93 GitHubIssueMapper:** Domain service to map Neo4j UUIDs to GitHub Issue numbers.
- [x] **#94 ConnectivityManager & SyncQueue:** Offline-first guard that queues actions during outages.
- [x] **#95 WebhookSignatureValidator:** Secure endpoint for real-time bidirectional sync from GitHub.
- [x] **#96 MarkdownTransformer:** Convert Graph Analysis results into GitHub-flavored Markdown.
- [x] **#97 SecretManager:** Secure handling of GitHub Personal Access Tokens via environment injection.

---

### v0.8.0 Agent Observability

- [x] **#78 AI Reasoning Logs:** In-issue Markdown summaries explaining architectural choices.
- [x] **#79 Live Agent Documentation:** Dynamic Progress Manifest with TODO, Files, Technical Debt.
- [x] **#80 Graph Visualization:** Interactive graph view of issues, components, and dependencies.
- [x] **#81 Agent Lifecycle Integration:** Full tracking of agent_working state with start/finish timestamps.

---

### v0.8.0 Policy Enforcement

- [x] **#82 Active Policy Enforcement:** Block API/CLI writes if they violate Architectural Rules.
- [x] **#83 Dependency Guard:** Real-time prevention of circular dependencies.
- [x] **#84 Graph Policy Engine:** "Rules of the Graph" enforced at write time.
- [x] **#85 Pre-Execution Validation:** Tasker blocks actions that violate architectural policies.
- [x] **#126 Constraints Configuration System:** Config file (`tasker.constraints.yml`) with enforcement levels.

---

### v0.8.0 API Enhancements

- [x] **#65 Workable Issues Endpoint:** `/api/v1/workable-issues` - Issues ready to work on.
- [x] **#66 Neo4j Status in Health:** Detailed connectivity status in `/health`.
- [x] **#67 Data Reset Endpoint:** `/api/v1/admin/reset` for testing.
- [x] **#68 Component Impact Analysis:** `/api/v1/analyze/component-impact/{id}`.
- [x] **#69 API Key Authentication:** `X-API-Key` header + `TASKER_AUTH_ENABLED`.
- [x] **#70 Dependency Graph:** `/api/v1/graph/dependencies` for visualization.
- [x] **#71 Issue PATCH:** Full status/priority/description/label updates.
- [x] **#72 Project Dashboard:** `/api/v1/projects/{name}/summary`.

---

### v0.8.0 Bug Fixes & Improvements

- [x] **#98 Fix CLI Test Failures:** Pre-existing test issues resolved.
- [x] **#99 Fix API Pagination:** Consistent format `{data: {items: [], total: N}}`.
- [x] **#100 Fix Analysis Endpoints:** `/analyze/impact` and `/component-impact` return 200.
- [x] **#101 Fix API Version:** Health shows correct version 0.8.0.
- [x] **#102 Input Validation:** XSS and Neo4j injection prevention.
- [x] **#103 Fix Webhook Endpoint:** Changed to GET for testing.
- [x] **#104 Missing API Routes:** Fixed duplicate route prefixes.
- [x] **#105 Integrate WebhookValidator:** Use centralized service.
- [x] **#106 Integrate SecretManager:** Centralized credential management.
- [x] **#107 API Authentication:** Middleware with `TASKER_AUTH_ENABLED`.
- [x] **#108 Rate Limiting:** Configurable per-minute limits.
- [x] **#109 Token Validation Length:** Changed to 36 characters minimum.
- [x] **#110 Dependency Validation:** Verified working.
- [x] **#111 Integration Tests:** Fixed credentials, 12/14 passing.
- [x] **#112 CLI Test Failures:** Pre-existing failures identified.
- [x] **#113 API Version:** Corrected in Docker.
- [x] **#114 Analysis 404:** Fixed in routes.
- [x] **#115 Admin Reset 404:** Fixed endpoint registration.
- [x] **#116 Pagination Format:** Consistent structure.
- [x] **#117 API Version Docker:** Rebuild with latest code.
- [x] **#118 Webhook Test 404:** Fixed route.
- [x] **#119 Sync Status 404:** Added httpx to runtime deps.
- [x] **#120 Docker Integration Tests:** Verified dependencies in container.
- [x] **#121 Sync Dependency Health:** Health check for httpx dependency.
- [x] **#122 Admin Endpoint Authentication:** Admin routes require auth.
- [x] **#123 Webhook Secret Validation:** Enforce webhook secrets.
- [x] **#124 Coverage 70%:** Increased test coverage.
- [x] **#125 Document Pagination:** API docs format documented.
- [x] **#131 CLI Priority Case Insensitive:** Accept case-insensitive priority input.
- [x] **#132 API Missing Import:** Add ComponentImpactIssueSummary to imports.
- [x] **#133 API Router Fix:** Fix router path registrations.
- [x] **#134 CLI Component Name Lookup:** Support component name lookup in show command.
- [x] **#135 API Duplicate Routes:** Add unique operation_id to duplicate routes.
- [x] **#136 CLI Component Update Name:** Support name lookup in component update command.
- [x] **#137 CLI Dependency Add Title:** Support title lookup for short issue IDs.
- [x] **#138 CLI Component Delete Name:** Use resolve_component_id in delete command.
- [x] **#139 API Component Impact Short ID:** Support short IDs and names in component-impact endpoint.
- [x] **#140 Test Exit Code Fix:** Update test_component_show_missing to expect exit code 2.
- [x] **#141 Linter F821 Fix:** Add UUID and Any imports to resolve undefined name errors.
- [x] **#142 Linter F401 Fix:** Remove unused imports and variables.
- [x] **#143 Linter F541, B904 Fix:** Fix f-strings without placeholders and add raise from err.
- [x] **#144 Linter I001, E501 Fix:** Auto-sort imports and fix long lines.
- [x] **#145 Docker Frontend Fix:** Add retry logic to npm ci in frontend Dockerfile.
- [x] **#167 Tasker Init docker-compose:** Generate full stack (Neo4j + API + Frontend)
- [x] **#175 Frontend Build in Scaffold:** Scaffolder copies frontend/dist/ to tasker/frontend/
- [x] **#177 API Auth Header Flexibility:** API accepts both X-API-Key and Authorization: Bearer headers
- [x] **#178 Frontend Package Assets:** Compiled Vue Kanban board included in package assets for scaffolding
- [x] **#183 Reduce Setup Friction:** docker-compose.yml uses env vars with sensible defaults for local dev

---

## Upcoming Milestones

### v1.0.0 - The "Architect" (Production Ready)

**Focus:** Reliability, Concurrency, and Global Scale.

- [ ] **Governance Closure Validation:** Mandatory check for "Solution Summary" and "File Impact" before closing.
- [ ] **Transaction Boundaries:** Implement atomic multi-operation commits (ACID) in Neo4j.
- [ ] **Neo4j Aura Stability:** 100% test pass rate on cloud-managed instances.
- [ ] **E2E Test Suite:** Complete end-to-end testing.
- [ ] **Stable API (v1):** Locked API contracts, strict MAJOR versioning.
- [ ] **IDE Integration:** Native extensions for Cursor, VS Code, Windsurf.
- [ ] **Autonomous Git Operations:** Full lifecycle from Issue to PR merging.
- [ ] **Project Master Config:** Single file defining system architecture.
- [ ] **Community Demos:** Production-ready boilerplate examples.

---

## Version Reference

| Version | Release Date | Status |
|---------|-------------|--------|
| 0.1.0 | 2024-02 | Initial |
| 0.2.0 | 2024-04 | Graph Base |
| 0.3.0 | 2024-06 | CLI + API |
| 0.4.0 | 2024-08 | Analysis |
| 0.5.0 | 2025-01 | Graph-Only |
| 0.6.0 | 2025-04 | Docker |
| 0.7.0 | 2025-10 | GitHub |
| **0.8.0** | **2026-04-23** | **Current** |
| 0.8.1 | 2026-04-12 | Upcoming - Lint cleanup |

---

## How We Version

| Type | Increment | Description |
| :--- | :--- | :--- |
| **MAJOR** | `1.0.0` | Breaking changes (enforced after v1.0.0). |
| **MINOR** | `0.1.0` | New features, rule additions, UI enhancements. |
| **PATCH** | `0.0.1` | Bug fixes, documentation, internal refactors. |

---

**Building the future of software engineering, one node at a time.**