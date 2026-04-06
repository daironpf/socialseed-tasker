# 📓 Changelog - SocialSeed Tasker

All notable changes to **SocialSeed Tasker** will be documented in this file.
This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

---

## [0.1.0] - 2026-01-15
### Added
- Initial project structure.
- Basic Neo4j connection tests.
- Conceptual design of the SocialSeed knowledge graph.