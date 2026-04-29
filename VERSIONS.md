# 📋 SocialSeed Tasker: Release Versioning Strategy

This document defines the milestones and release strategy for **SocialSeed Tasker**. We strictly follow [Semantic Versioning (SemVer)](https://semver.org/), ensuring every release communicates its stability level and functional scope to both human developers and AI agents.

---

## Versioning Policy

**Major Version Zero (0.y.z):** Per SemVer standards, while the project is in the `0.y.z` phase, the API and core structures are considered unstable.

**"Strict Major" Rule:** Enforcement of MAJOR version increments for breaking changes will officially begin **only after the release of version 1.0.0**.

Until then, breaking changes may occur in MINOR releases (`0.x.0`) to allow rapid architectural evolution.

---

## Version Reference

| Version | Date | Focus |
|---------|------|-------|
| 0.1.0 | 2024-02 | Initial structure, Neo4j connection tests |
| 0.2.0 | 2024-04 | Graph base |
| 0.3.0 | 2024-06 | CLI + API |
| 0.4.0 | 2024-08 | Graph Analysis |
| 0.5.0 | 2025-01-15 | **Graph-Only** - Neo4j exclusive storage |
| 0.5.1 | 2026-04-07 | Post-Release Updates |
| 0.6.0 | 2026-04-08 | **Polish & Alignment** |
| 0.7.0 | 2025-10 | GitHub Integration base |
| 0.8.0 | 2026-04-23 | **Observability & Active Governance** |
| **0.8.1** | **2026-04-27** | **Polish & Documentation** |

---

## 🚀 v0.8.0 - The "Observability & Active Governance"

**Status:** Released on 2026-04-23

SocialSeed Tasker is a **Graph-Only** platform, using Neo4j as its exclusive source of truth.

**Focus:** Human-in-the-loop transparency and active enforcement.

**Test Coverage:** 270+ unit tests passing

---

### Core Infrastructure

- [x] **Neo4j as Exclusive Storage:** File storage removed, only Neo4j backend supported
- [x] **Graph Traversal (BFS):** Dependency chain analysis, circular dependency detection, blocked issues
- [x] **Human-Centric UI:** Vue.js Kanban board with drag & drop, auto-refresh, agent_working indicator
- [x] **REST API for AI Agents:** Full CRUD for issues, components, dependencies with consistent error envelopes
- [x] **CLI Interface:** Typer + Rich CLI with issue, component, dependency, and analysis commands
- [x] **Root Cause Analysis:** Scoring system with component match, temporal recency, label overlap, semantic similarity, graph proximity
- [x] **Impact Analysis:** BFS for direct/transitive dependents, blocked issues detection, risk levels (LOW/MEDIUM/HIGH/CRITICAL)
- [x] **Docker Compose:** Three services (Neo4j, API, Frontend) with health checks and networking
- [x] **Project Scaffolding:** `tasker init` to inject Tasker infrastructure into external projects
- [x] **Neo4j Aura DB Support:** Auto-detection of encryption mode from URI (bolt+s://, neo4j+s://)
- [x] **Agent Working Indicator:** `agent_working` field with UI indicator (cyan robot icon)
- [x] **AI Agent Workflow:** REST API with OpenAPI docs, consistent JSON envelopes, progress tracking via issue descriptions
- [x] **Advanced Cypher Queries:** Impact analysis with BFS, blocked issues detection, affected components collection, risk level calculation
- [x] **Architectural Analysis Module:** Rule-based analyzer for forbidden technologies, required patterns, forbidden dependencies, max dependency depth
- [x] **Short ID Resolution:** Support for short UUID aliases in `show` and `update` commands
- [x] **API Health Endpoint:** `/health` with Neo4j connectivity status
- [x] **Project Filter:** Filter by project name in API and CLI
- [x] **Demo Mode:** Auto-seed sample data with `TASKER_DEMO_MODE`
- [x] **Bulk Dependencies:** API endpoint to create multiple dependencies in one request
- [x] **Component Name Lookup:** `name` query parameter in GET /components
- [x] **Optional Component:** Create issues without component (uses 'uncategorized' default)
- [x] **Duplicate Detection:** Warn when creating issues with duplicate titles in same component

---

### GitHub Integration (#88-#97)

- [x] **#88 GitHub API Adapter:** Hexagonal Adapter mapping Tasker Issues to GitHub Issues/Milestones
- [x] **#89 Bidirectional Webhook Listener:** API endpoint for real-time GitHub updates
- [x] **#90 Causal Mirroring:** Automatic sync of Tasker Analysis as GitHub Issue comments
- [x] **#91 Offline-First Sync Engine:** Queue system to batch local changes and push when online
- [x] **#92 Label-to-Graph Mapping:** Sync GitHub Labels directly into Neo4j nodes
- [x] **#93 GitHubIssueMapper:** Domain service mapping Neo4j UUIDs to GitHub Issue numbers
- [x] **#94 ConnectivityManager & SyncQueue:** Offline-first guard queuing actions during outages
- [x] **#95 WebhookSignatureValidator:** Secure endpoint for real-time bidirectional GitHub sync
- [x] **#96 MarkdownTransformer:** Convert Graph Analysis to GitHub-flavored Markdown
- [x] **#97 SecretManager:** Secure GitHub PAT handling via environment injection

---

### Agent Observability (#78-#81)

- [x] **#78 AI Reasoning Logs:** In-issue Markdown summaries explaining architectural choices
- [x] **#79 Live Agent Documentation:** Dynamic Progress Manifest with TODO, Files, Technical Debt

  ```markdown
  ## Agent Progress Manifest
  
  ### Live TODO
  - [ ] Sub-task 1
  - [x] Sub-task 2
  
  ### Affected Files
  - src/core/module.ts
  - tests/unit/test_module.py
  
  ### Technical Debt Notes
  - Note about temporary workaround
  - TODO for future refactoring
  ```

- [x] **#80 Graph Visualization:** Interactive graph view of issues, components, dependencies (vis-network)
- [x] **#81 Agent Lifecycle Integration:** Full tracking of `agent_working` state with start/finish timestamps

---

### Policy Enforcement (#82-#85, #126)

- [x] **#82 Active Policy Enforcement:** Block API/CLI writes if they violate Architectural Rules
- [x] **#83 Dependency Guard:** Real-time prevention of circular dependencies
- [x] **#84 Graph Policy Engine:** "Rules of the Graph" enforced at write time
- [x] **#85 Pre-Execution Validation:** Tasker blocks actions violating architectural policies
- [x] **#126 Constraints Configuration System:** Config file (`tasker.constraints.yml`) with enforcement levels

---

### API Enhancements (#65-#72)

- [x] **#65 Workable Issues Endpoint:** `/api/v1/workable-issues` - Issues ready to work on
- [x] **#66 Neo4j Status in Health:** Detailed connectivity status in `/health`
- [x] **#67 Data Reset Endpoint:** `/api/v1/admin/reset` for testing
- [x] **#68 Component Impact Analysis:** `/api/v1/analyze/component-impact/{id}`
- [x] **#69 API Key Authentication:** `X-API-Key` header + `TASKER_AUTH_ENABLED`
- [x] **#70 Dependency Graph:** `/api/v1/graph/dependencies` for visualization
- [x] **#71 Issue PATCH:** Full status/priority/description/label updates
- [x] **#72 Project Dashboard:** `/api/v1/projects/{name}/summary`

---

### Bug Fixes & Improvements (#98-#183)

#### Critical Fixes
- [x] **#98** Fix CLI Test Failures
- [x] **#99** Fix API Pagination - Consistent format `{data: {items: [], total: N}}`
- [x] **#100** Fix Analysis Endpoints
- [x] **#101** Fix API Version - Health shows correct version
- [x] **#102** Input Validation - XSS and Neo4j injection prevention
- [x] **#103** Fix Webhook Endpoint
- [x] **#104** Missing API Routes
- [x] **#105** Integrate WebhookValidator
- [x] **#106** Integrate SecretManager
- [x] **#107** API Authentication middleware
- [x] **#108** Rate Limiting - Configurable per-minute limits
- [x] **#109** Token Validation Length - 36 characters minimum
- [x] **#110** Dependency Validation
- [x] **#111** Integration Tests - 12/14 passing
- [x] **#112** CLI Test Failures
- [x] **#113-#118** Various route and endpoint fixes
- [x] **#119** Sync Status 404 - Added httpx to runtime deps
- [x] **#120** Docker Integration Tests
- [x] **#121** Sync Dependency Health
- [x] **#122** Admin Endpoint Authentication
- [x] **#123** Webhook Secret Validation

#### Quality & Polish
- [x] **#124** Coverage 70%
- [x] **#125** Document Pagination
- [x] **#131-#144** CLI and API improvements (short UUID, name lookup, linter fixes)
- [x] **#145** Docker Frontend Fix

#### Scaffolding Enhancements
- [x] **#167** Tasker Init docker-compose - Generate full stack (Neo4j + API + Frontend)
- [x] **#175** Frontend Build in Scaffold
- [x] **#177** API Auth Header Flexibility - Both X-API-Key and Authorization: Bearer
- [x] **#178** Frontend Package Assets - Compiled Vue Kanban included
- [x] **#183** Reduce Setup Friction - Sensible defaults in docker-compose.yml

---

## v0.8.1 - "Polish & Documentation" (Released - April 27, 2026)

**Status:** Released on 2026-04-27

**Focus:** Code quality, documentation, and performance monitoring.

**Test Coverage:** 454 unit tests passing (61%)

---

### Code Quality (#193)

- [x] Migrated to new ruff config format (`[tool.ruff.lint]` section)
- [x] Fixed variable naming issues (`l` → `label`)
- [x] Fixed whitespace issues (trailing whitespace, blank lines with whitespace)
- [x] Fixed unused variables (prefixed with underscore)
- [x] Combined nested if statements (SIM102)
- [x] Added exception chaining (`from None`)
- [x] Formatted code with ruff format

---

### API Documentation (#194)

- [x] Enhanced API description in `app.py` with Key Features section
- [x] Added authentication requirements to OpenAPI docs
- [x] Added OpenAPI discovery endpoints (`/docs`, `/redoc`, `/openapi.json`)
- [x] Enhanced OpenAPI tags with detailed descriptions
- [x] Added docstrings with examples to key endpoints:
  - `create_issue`: Args, Returns, Raises, curl example
  - `get_issue`: Detailed field descriptions
  - `list_issues`: Pagination with JSON example
  - `update_issue`: Partial update documentation
- [x] Enhanced schema descriptions (`IssueCreateRequest`, `IssueUpdateRequest`, `DependencyRequest`, `ComponentCreateRequest`)

---

### CLI UX Improvements (#195)

- [x] Documented CLI blank lines limitation in module docstring
- [x] Enhanced error messages with suggestions
- [x] Added multiple match handling for short IDs
- [x] Added context tips for dependency errors
- [x] Added `💡 Tip:` suggestions throughout

---

### Test Coverage (#196)

- [x] Created new test file `tests/unit/test_ai_rag.py` with 25 tests
- [x] Added tests for AI/RAG endpoints (search-context, similar-issues, embeddings)
- [x] Added tests for Deployment endpoints
- [x] Added tests for Agent Lifecycle endpoints
- [x] Added tests for Manifest endpoints (TODO, files, notes)
- [x] Added tests for Label endpoints

**Test Results:**
- Before: 429 tests, 59% coverage
- After: 454 tests, 61% coverage (+2%)

---

### Performance Optimization (#197)

- [x] Added performance monitoring middleware
- [x] Added `X-Response-Time-Ms` header to all responses
- [x] Added slow request logging with configurable threshold
- [x] Added Neo4j indexes for frequently queried properties:
  - `issue_created_at`, `issue_project`, `component_name`, `component_project`
  - `deployment_commit`, `deployment_environment`
- [x] Added optimized BFS query (`IMPACT_ANALYSIS_BFS`) with depth limit (3)
- [x] Added pagination query with `USING INDEX` hints
- [x] Added `COUNT_ISSUES` for efficient pagination
- [x] Documented performance targets

---

### Security & Dependencies (#198)

- [x] Created `.github/workflows/dependency-update.yml`:
  - Weekly scheduled dependency updates (Sundays at midnight)
  - Manual trigger via `workflow_dispatch`
  - Jobs: `update-dependencies`, `security-audit`, `lint-and-test`
- [x] Created `SECURITY.md`:
  - Security checklist (8 items verified)
  - Dependency upgrade policy
  - Environment variables for security
  - Docker security notes
  - Security issue reporting procedure
- [x] Added `pip-audit>=0.1.0` to dev dependencies

---

## v0.9.0 - "Memory & Intelligence" (Q3 2026)

**Focus:** Long-term memory and code context

### Key Features

#### Code-as-Graph (Tree-sitter Integration)
Map the entire repository as a graph structure:

- **Node Types:** `File`, `Class`, `Function`, `Import`, `Test`
- **Relationship Types:** `[:CALLS]`, `[:DEPENDS_ON]`, `[:DEFINES]`, `[:TESTS]`, `[:CONTAINS]`

- [ ] Tree-sitter parser integration for multi-language support
- [ ] Incremental scanning (changed files only)
- [ ] Git-aware (file history tracking)
- [ ] Symbol index for fast lookups

#### RAG Native in Graph (Vector Indexes)
Enable semantic search across project knowledge:

- [ ] Neo4j vector indexes for task embeddings
- [ ] Solution similarity matching
- [ ] Historical solution retrieval
- [ ] Context injection for agent prompts

#### AI Reasoning Logs
Record agent reasoning patterns: `(Agent)-[:THOUGHT]->(ReasoningNode)-[:DECIDED]->(Task)`

- [ ] ReasoningNode with `thought`, `confidence`, `alternatives_considered`
- [ ] Automatic capture via API interceptors
- [ ] Human review and feedback loop

---

## 🚀 v1.0.0 - "The Architect" (Production Ready - 2027)

**Focus:** Enterprise stability, Governance, and MCP Protocol

### Key Features

#### MCP Server (Model Context Protocol)
- [ ] Standard MCP protocol compliance
- [ ] Direct graph context access
- [ ] Claude Desktop integration
- [ ] Cursor integration
- [ ] Custom AI assistant support

#### Guardrails & Enforcement
- [ ] Strict blocking of operations violating defined architecture
- [ ] Governance Closure Validation (verify Solution Summary before close)
- [ ] Dynamic RBAC: `JuniorAgent`, `SeniorAgent`, `SecurityAgent`

#### Token Budget Management
- [ ] `estimated_cost` and `actual_cost` tracking
- [ ] Per-project/agent budget limits
- [ ] Auto-pause on limit reached
- [ ] Cost attribution by issue/component

#### Stable API v1
- [ ] Locked API contracts
- [ ] Strict SemVer versioning
- [ ] Deprecation policy
- [ ] Breaking change communication

#### IDE Integration
- [ ] VS Code Extension with issue panel and dependency viewer
- [ ] Cursor/Windsurf with real-time suggestions
- [ ] Inline architecture rule highlights

#### Autonomous Git Operations
- [ ] Issue → Branch → Development → PR → Merge
- [ ] Graph-verified approvals
- [ ] Automatic branch management

#### Enterprise Features
- [ ] Project Master Config (YAML defining architecture)
- [ ] Multi-Tenant SaaS support
- [ ] Community demo boilerplates
- [ ] Complete E2E Test Suite

---

## Versioning Table

| Type | Increment | Description |
| :--- | :--- | :--- |
| **MAJOR** | `1.0.0` | Breaking changes (enforced after v1.0.0) |
| **MINOR** | `0.1.0` | New features, rule additions, UI enhancements |
| **PATCH** | `0.0.1` | Bug fixes, documentation, internal refactors |

---

## 💡 CTO Implementation Notes

### Critical Considerations for v0.9.0 - v1.0.0:

1. **Atomicity:** All graph updates by agents must be treated as ACID transactions. If architecture validation fails, the change must not persist.

2. **Sanitization:** The RAG system must filter secrets and API keys before generating embeddings to prevent data leaks to LLMs. Never store raw credentials in vector indexes.

3. **Synchronization:** The `WebhookSignatureValidator` implementation is critical for secure and reliable GitHub sync in production.

4. **Setup Friction:** Default to Neo4j local with sensible env vars as the happy path. The `docker-compose.yml` must work out-of-the-box for new users.

5. **Agent Trust Levels:** Different roles require different trust levels:
   - JuniorAgents: More enforcement, require approval for critical operations
   - SeniorAgents: Can override with justification
   - SecurityAgents: Define rules, block operations, cannot override audit logs

---

**Building the future of software engineering, one node at a time.** 🛡️🕸️