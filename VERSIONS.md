# Release Versioning Strategy - SocialSeed Tasker

This document defines the versioning milestones for **SocialSeed Tasker**. We strictly follow [Semantic Versioning (SemVer)](https://semver.org/), ensuring that every release communicates its level of stability and functional scope to both human developers and AI agents.

---

## Versioning Policy Note

**Major Version Zero (0.y.z):** Per SemVer standards, while the project is in the `0.y.z` phase, the API and core structures are considered unstable. 
* **The "Strict Major" rule:** Enforcement of MAJOR version increments for breaking changes will officially begin **only after the release of version 1.0.0**. 
* Until then, breaking changes may occur in MINOR releases (`0.x.0`) to allow for rapid architectural evolution.

---

## Current Milestone: v0.6.0 (The "Polish & Alignment" Release)

**Status:** *Released* on 2026-04-08

SocialSeed Tasker is a **Graph-Only** platform, leveraging Neo4j as its exclusive source of truth.

* **Focus:** Stabilizing the Neo4j engine, Graph traversal (BFS), and the Human-Centric UI.
* **Audit Status:** 147 unit tests passing (0 failures).
* **Key Goal:** Providing high-performance, relationship-aware infrastructure for AI-native development.

### v0.5.x Checklist (Completed in previous releases)

* [x] **Neo4j as Exclusive Storage:** File storage removed, only Neo4j backend supported.
* [x] **Graph Traversal (BFS):** Dependency chain analysis, circular dependency detection, blocked issues.
* [x] **Human-Centric UI:** Vue.js Kanban board with drag & drop, auto-refresh, agent_working indicator.
* [x] **REST API for AI Agents:** Full CRUD for issues, components, dependencies with consistent error envelopes.
* [x] **CLI Interface:** Typer + Rich CLI with issue, component, dependency, and analysis commands.
* [x] **Root Cause Analysis:** Scoring system with component match, temporal recency, label overlap, semantic similarity, graph proximity.
* [x] **Impact Analysis:** BFS for direct/transitive dependents, blocked issues detection, risk levels (LOW/MEDIUM/HIGH/CRITICAL).
* [x] **Docker Compose:** Three services (Neo4j, API, Frontend) with health checks and networking.
* [x] **Project Scaffolding:** `tasker init` command to inject Tasker infrastructure into external projects.
* [x] **Neo4j Aura DB Support:** Auto-detection of encryption mode from URI (bolt+s://, neo4j+s://).
* [x] **Agent Working Indicator:** `agent_working` field with UI indicator (cyan robot icon).
* [x] **AI Agent Workflow:** REST API with OpenAPI docs, consistent JSON envelopes, progress tracking via issue descriptions.
* [x] **Advanced Cypher Queries:** Impact analysis with BFS for direct/transitive dependents, blocked issues detection, affected components collection, and risk level calculation (LOW/MEDIUM/HIGH/CRITICAL).
* [x] **Architectural Analysis Module:** Rule-based analyzer for forbidden technologies, required patterns, forbidden dependencies, and max dependency depth validation.
* [x] **Short ID Resolution:** Support for short UUID aliases in `show` and `update` commands.
* [x] **API Health Endpoint:** Implement `/health` with Neo4j connectivity status.
* [x] **Documentation Sync:** Align CLI help strings with actual API schemas (Added /analyze/link-test endpoint).
* [x] **Neo4j Performance:** Optimization of Cypher queries for deep relationship traversal.
* [x] **Project Filter:** Add filtering by project name to issue list API and CLI.
* [x] **Demo Mode:** Auto-seed sample data on first startup with `TASKER_DEMO_MODE` env var.
* [x] **Bulk Dependencies:** API endpoint to create multiple dependencies in one request.
* [x] **Component Name Lookup:** Add name query parameter to GET /components endpoint.
* [x] **Optional Component:** Allow creating issues without component (uses 'uncategorized' default).
* [x] **Duplicate Detection:** Warn when creating issues with duplicate titles in same component.

---

## Upcoming Milestones

### v0.8.0 - The "Observability & Active Governance" Release

**Focus:** Human-in-the-loop transparency and enforcement.

* [ ] **AI Reasoning Logs:** In-issue Markdown summaries explaining why the AI chose a specific architectural path based on the graph.
* [ ] **Live Agent Documentation:** Agents must maintain a "Dynamic Progress Manifest" within the issue description, including:
    * Live TODO List: Checkboxes updated as the agent completes sub-tasks.
    * Affected Files: Real-time list of created or modified files.
    * Technical Debt Notes: Observations made by the agent during implementation.
* [ ] **Graph Visualization:** Interactive graph view of issues, components, and dependencies (beyond Kanban).
* [ ] **Agent Lifecycle Integration:** Full tracking of the `agent_working` state with start/finish timestamps.
* [ ] **Active Policy Enforcement:** Block API/CLI writes if they violate defined Architectural Rules (forbidden tech, depth, etc.).
* [ ] **Dependency Guard:** Real-time prevention of circular dependencies during issue creation.
* [ ] **Graph Policy Engine:** Define "Rules of the Graph" (e.g., Layer A cannot touch Layer C) enforced at write time.
* [ ] **Pre-Execution Validation:** Tasker automatically blocks agent actions that violate defined architectural policies.
* [ ] **Automated Self-Healing:** Integration with `socialseed-e2e` to trigger "Fix Issues" automatically when tests fail.
* [ ] **Swarm Coordination:** Multi-agent role management (Planner, Developer, Reviewer) synchronized via Graph states.
* [ ] **GitHub Integration:** 
    * GitHub API Adapter: Implementation of a Hexagonal Adapter to map Tasker Issues to GitHub Issues/Milestones.
    * Bidirectional Webhook Listener: API endpoint to receive real-time updates from GitHub (comments, label changes, status updates).
    * Causal Mirroring: Automated sync of Tasker's "Analysis" (Root Cause/Impact) as comments in GitHub Issues for human reviewers.
    * Offline-First Sync Engine: Queue system to batch local changes and push them to GitHub once internet connection is restored.
    * Label-to-Graph Mapping: Syncing GitHub Labels directly into Neo4j nodes for enhanced filtering.
    * GitHubIssueMapper: Domain service to map Neo4j UUIDs to GitHub Issue numbers and metadata.
    * ConnectivityManager & SyncQueue: Offline-first "Guard" that queues agent actions during power/internet outages and flushes them to the cloud upon reconnection.
    * WebhookSignatureValidator: Secure endpoint for real-time bidirectional sync from GitHub.
    * MarkdownTransformer: Convert Graph Analysis results into GitHub-flavored Markdown (Tables and Mermaid diagrams).
    * SecretManager: Secure handling of GitHub Personal Access Tokens (PAT) via environment injection.

### v1.0.0 - The "Architect" (Production Ready)

**Focus:** Reliability, Concurrency, and Global Scale.

* [ ] **Governance Closure Validation:** Mandatory check for "Solution Summary" and "File Impact" documentation before allowing an agent to close an issue.
* [ ] **Transaction Boundaries:** Implement atomic multi-operation commits (ACID) natively in Neo4j.
* [ ] **Neo4j Aura Stability:** 100% test pass rate on cloud-managed graph instances with full encryption.
* [ ] **E2E Test Suite:** Complete end-to-end testing of the Tasker workflow from CLI to Aura DB.
* [ ] **Stable API (v1):** Locked API contracts and start of strict MAJOR versioning.
* [ ] **IDE Integration (Plugins):** Native extensions for **Cursor, VS Code, and Windsurf** to interact with the Tasker API.
* [ ] **Autonomous Git Operations:** Full lifecycle management from Issue creation to PR merging with graph-verified approvals.
* [ ] **Project "Master Config" (YAML-to-Graph):** A single file that defines the entire system architecture, which Tasker then enforces.
* [ ] **Community Demos:** Production-ready boilerplate examples (E-commerce, SaaS API) managed entirely by SocialSeed Tasker.

---

## How We Version

| Type | Increment | Description |
| :--- | :--- | :--- |
| **MAJOR** | `1.0.0` | Breaking changes or fundamental shifts (Enforced after v1.0.0). |
| **MINOR** | `0.1.0` | New features, rule additions, or UI enhancements. |
| **PATCH** | `0.0.1` | Bug fixes, documentation updates, or internal refactors. |

---

**Building the future of software engineering, one node at a time.**
