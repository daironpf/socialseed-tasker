# 🏷️ Release Versioning Strategy - SocialSeed Tasker

This document defines the versioning milestones for **SocialSeed Tasker**. We strictly follow [Semantic Versioning (SemVer)](https://semver.org/), ensuring that every release communicates its level of stability and functional scope to both human developers and AI agents.

---

## ⚠️ Versioning Policy Note
**Major Version Zero (0.y.z):** Per SemVer standards, while the project is in the `0.y.z` phase, the API and core structures are considered unstable. 
* **The "Strict Major" rule:** Enforcement of MAJOR version increments for breaking changes will officially begin **only after the release of version 1.0.0**. 
* Until then, breaking changes may occur in MINOR releases (`0.x.0`) to allow for rapid architectural evolution.

---

## 🚀 Current Milestone: v0.5.x (The Graph-Native Foundation)
**Status:** *Active Development / Beta*

**Note:** As of the latest audit, local file storage support has been deprecated. SocialSeed Tasker is now a **Graph-Only** platform, leveraging Neo4j as its exclusive source of truth.

* **Focus:** Stabilizing the Neo4j engine, Graph traversal (BFS), and the Human-Centric UI.
* **Audit Status:** Passed 178 unit tests (Refactored for Graph Persistence).
* **Key Goal:** Providing high-performance, relationship-aware infrastructure for AI-native development.

---

## 🛠️ Upcoming Milestones

### v0.6.0 — The "Polish & Alignment" Release
**Focus:** Quality Assurance and Developer Experience (DX).
* [ ] **Short ID Resolution:** Support for short UUID aliases in `show` and `update` commands.
* [ ] **API Health & Consistency:** Implement `/health` endpoint and fix route prefix mismatches (`/api/v1/dependencies`).
* [ ] **Documentation Sync:** Align CLI help strings with actual API schemas.
* [ ] **Neo4j Performance:** Optimization of Cypher queries for deep relationship traversal.

### v0.8.0 — The "Observability & Active Governance" Release
**Focus:** Human-in-the-loop transparency and enforcement.
* [ ] **Agent Progress Manifest:** Implementation of dynamic Markdown updates within issues (TODO lists, modified files, reasoning logs).
* [ ] **Active Policy Enforcement:** Block API/CLI writes if they violate defined Architectural Rules (forbidden tech, depth, etc.).
* [ ] **Agent Lifecycle Integration:** Full tracking of the `agent_working` state with start/finish timestamps.
* [ ] **Dependency Guard:** Real-time prevention of circular dependencies during issue creation.
* [ ] **Graph Visualization:** Interactive node-link view in the Dashboard using the Neo4j schema.

### v1.0.0 — The "Architect" (Production Ready)
**Focus:** Reliability, Concurrency, and Global Scale.
* [ ] **Governance Closure Validation:** Mandatory check for "Solution Summary" and "File Impact" documentation before allowing an agent to close an issue.
* [ ] **Transaction Boundaries:** Implement atomic multi-operation commits (ACID) natively in Neo4j.
* [ ] **Neo4j Aura Stability:** 100% test pass rate on cloud-managed graph instances with full encryption.
* [ ] **E2E Test Suite:** Complete end-to-end testing of the Tasker workflow from CLI to Aura DB.
* [ ] **Stable API (v1):** Locked API contracts and start of strict MAJOR versioning.

---

## 🔧 How We Version

| Type | Increment | Description |
| :--- | :--- | :--- |
| **MAJOR** | `1.0.0` | Breaking changes or fundamental shifts (Enforced after v1.0.0). |
| **MINOR** | `0.1.0` | New features, rule additions, or UI enhancements. |
| **PATCH** | `0.0.1` | Bug fixes, documentation updates, or internal refactors. |

---

**Building the future of software engineering, one node at a time.** 🛡️🕸️