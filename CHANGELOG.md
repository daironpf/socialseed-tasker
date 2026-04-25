# 📓 Changelog - SocialSeed Tasker

All notable changes to **SocialSeed Tasker** will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.8.0] - 2026-04-23 (Observability & UI Enhancements)

### Added
- **Interactive Dependency Graph:** Integrated `GraphView.vue` into the main dashboard, utilizing `vis-network` to visualize issue dependencies (`[:DEPENDS_ON]`) with force-directed and hierarchical layouts.
- **Advanced UI Filtering:** Added robust project-level filtering in the Kanban board to dynamically narrow down components and issues based on project context.
- **Seeding v2:** Upgraded `seed_issues_v2.py` to automatically scaffold connected dependency trees across different projects (e.g., `demo-platform`, `ecommerce-store`).

### Fixed
- **UI State Management:** Resolved reactive state bugs in `uiStore` to ensure instant visual updates when switching project filters.
- **Dependency Propagation:** Fixed issue where the initial seed script failed to insert Neo4j relationships.

---

## [0.6.0] - 2026-04-08 (Polish & Alignment Release)

### Added
- **Duplicate Issue Detection:** API now warns when creating issues with duplicate titles in the same component. The warning is returned in the response `meta.warnings` field.
- **Component Name Lookup:** Added `name` query parameter to `GET /components` endpoint to filter by exact component name.
- **Optional Component ID:** Issues can now be created without a `component_id`. If not provided, a default "uncategorized" component in the "system" project is created automatically.
- **New Analysis Endpoint:** Added `/api/v1/analyze/link-test` endpoint with clearer documentation. The old `/analyze/root-cause` is now marked as deprecated.

### Changed
- **API Response Meta:** Added `warnings` field to the response metadata for non-critical client notifications.
- **CLI Console:** Improved Console configuration with explicit width, no_color, and force_terminal settings.

### Known Limitations
- **CLI Blank Lines:** The CLI output shows extra blank lines at the start of commands. This is a known Typer/Rich integration issue with no current workaround.

---

## [0.5.1] - 2026-04-07 (Post-Release Updates)

### Added
- **Project Filter:** Filter issues by project name in both API (`?project=`) and CLI (`--project`).
- **Seed Data:** `tasker seed run` command to populate demo data (4 components, 8 issues, 6 dependencies).
- **Demo Mode:** `TASKER_DEMO_MODE=true` env var to auto-seed data on API startup.
- **Bulk Dependencies:** `POST /api/v1/issues/{id}/dependencies/bulk` endpoint for batch operations.
- **Component Names in CLI:** Issues now display component names instead of UUIDs in list outputs.
- **Dependencies in List Response:** Issue list API now populates `dependencies` and `blocks` fields from graph.

### Changed
- **Dockerfile:** Updated to use `__main__.py` with proper Neo4j repository initialization.
- **Release Workflow:** Added Docker image build and push to GitHub Container Registry (ghcr.io).
- **README Quick Start:** Added copy-paste demo flow with working curl commands.

### Fixed
- **Short UUID Resolution:** CLI `show` and `close` commands now support short UUID prefixes.
- **Docker Image Version:** Fixed stale version in Docker health endpoint (now reports v0.5.0).

---

## [0.5.0] - 2026-04-06 (Full Functional Audit)

### Added
- **Graph-Native Architecture:** Transitioned to a 100% Neo4j-backed system. 
- **Core Hexagonal Architecture:** Full implementation of Feature-Oriented layers (API, Domain, Infrastructure).
- **Human-Centric Board:** Vue.js Kanban dashboard with drag-and-drop, 10s auto-refresh, and real-time agent activity indicator.
- **Advanced Graph Analytics:** - **Root Cause Analysis:** Graph proximity (BFS) + Temporal + Semantic scoring.
    - **Impact Analysis:** Transitive dependency analysis with risk level calculation (LOW to CRITICAL).
- **CLI Suite:** Complete command set for `issue`, `component`, and `dependency` management with Rich output.
- **Scaffolding (`tasker init`):** CLI command to seed projects with AI Skills and auto-detect Docker/Neo4j configurations.
- **Architectural Rules Module:** Initial engine for forbidden patterns, required technologies, and max dependency depth.

### Fixed
- **Cypher Optimization:** Refactored relationship traversal queries for higher performance in deep graphs.
- **Dependency Validation:** Implemented BFS-based circular dependency detection to prevent deadlocks.
- **CLI Consistency:** Standardized all command outputs using the `Rich` library for better readability.

### Security
- **Aura DB Integration:** Auto-detection of encryption requirements from Neo4j URI strings.
- **Typed API Envelopes:** All REST responses now follow a consistent `{data, error, meta}` format.

### Removed
- **File Storage Backend:** Deprecated and removed support for local JSON file persistence. The project is now **Neo4j-Exclusive** to ensure data integrity and relationship-first logic.

### Testing
- **147 Unit Tests Passing:** Full test suite refactored with in-memory mock repositories for CLI, API, and bootstrap layers.
- **API Test Coverage:** All REST endpoints tested including health, CRUD, dependencies, analysis, and error envelopes.
- **CLI Test Coverage:** All commands tested (issue, component, dependency, status, init) with mock repository injection.

---

## [0.1.0] - 2026-01-15
### Added
- Initial project structure.
- Basic Neo4j connection tests.
- Conceptual design of the SocialSeed knowledge graph.