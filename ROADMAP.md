# 🗺️ SocialSeed Tasker: Strategic Roadmap

**SocialSeed Tasker** is an **AI-Native Project Management Framework** powered by **Neo4j**. Our mission is to evolve beyond flat task lists into **Graph-Based Architectural Governance** for autonomous software engineering. The Neo4j graph becomes the "consciousness" of the development process.

**Last updated:** 2026-04-27 | **Current Version:** v0.8.1 | **Next:** v0.9.0

---

## 📍 Phase 1: Foundation & Scaffolding ✅ COMPLETED (Q2 2026)

*Goal: Establish Tasker as the essential "Sidecar" for modern projects.*

### Core Infrastructure
- [x] **Hexagonal Architecture:** Implementation of API, Domain, and Infrastructure layers
- [x] **Injected Scaffolding:** `tasker init` CLI to inject infrastructure into existing projects
- [x] **Hybrid Persistence:** Support for local Neo4j and Aura DB Cloud
- [x] **Base Graph Analysis:** Root-Cause and Impact Analysis using BFS

### CLI & API
- [x] Full CLI: `issue`, `component`, `dependency`, `analysis`, `project` commands
- [x] Short UUID support in all commands (8+ chars)
- [x] FastAPI REST API with OpenAPI docs at `/docs`
- [x] Consistent response envelopes `{data, error, meta}` with pagination
- [x] Entry points: `tasker` and `socialseed-tasker`
- [x] Health endpoint `/health` with Neo4j connectivity status

### UI & Visualization
- [x] Vue.js Kanban board with drag & drop
- [x] Auto-refresh every 10 seconds
- [x] Real-time agent activity indicator
- [x] Interactive dependency graph with vis-network
- [x] Advanced project-level filtering

---

## 🧠 Phase 2: Graph Intelligence & Long-Term Memory (Q3 2026)

*Goal: Provide agents with deep context and historical memory.*

### Code-as-Graph (Tree-sitter Integration)
Map the entire repository as a graph structure for deep code understanding:

- [ ] **Node Types:**
  - `File` - Source files with path, language, lines of code
  - `Class` - Classes with methods and attributes
  - `Function` - Functions with parameters and return types
  - `Import` - Import statements and their targets
  - `Test` - Test files linked to tested units

- [ ] **Relationship Types:**
  - `[:CALLS]` - Function/Method invocations
  - `[:DEPENDS_ON]` - Import/Dependency relationships
  - `[:DEFINES]` - File defines Class/Function
  - `[:TESTS]` - Test file tests Class/Function
  - `[:CONTAINS]` - File contains Function/Class

- [ ] **Implementation Details:**
  - Tree-sitter parser integration for multi-language support
  - Incremental scanning (only changed files)
  - Git-aware (track file history)
  - Symbol index for fast lookups

### RAG Native in Graph (Vector Indexes)
Enable semantic search across all project knowledge:

- [ ] **Vector Indexes in Neo4j:**
  - Store embeddings for tasks and past solutions
  - Support for task similarity matching
  - Historical solution retrieval

- [ ] **RAG Pipeline:**
  - Embedding generation service
  - Chunking strategies for code/documents
  - Vector similarity search
  - Context injection for agent prompts

- [ ] **Knowledge Types:**
  - Past issue solutions
  - Architectural decisions (ADRs)
  - Test patterns and examples
  - Configuration best practices

### Agentic Traceability (Thinking Logs)
Record agent reasoning in the graph for transparency and learning:

- [ ] **Pattern:** `(Agent)-[:THOUGHT]->(ReasoningNode)-[:DECIDED]->(Task)`
  
- [ ] **ReasoningNode Properties:**
  - `thought`: The agent's reasoning text
  - `confidence`: Confidence score (0-1)
  - `alternatives_considered`: Other options evaluated
  - `rejected_reasons`: Why alternatives were rejected
  - `timestamp`: When the thought occurred

- [ ] **Trace Integration:**
  - Automatic capture via API interceptors
  - Manual logging via agent manifest
  - Human review and feedback loop
  - Learning from past decisions

### Live Documentation (v0.8.0 ✅)
- [x] **Dynamic Progress Manifest** in issue description:
  - Live TODO List with checkboxes
  - Affected Files in real-time
  - Technical Debt Notes
- [ ] Standardized templates for agent documentation

### Observability (v0.8.0 ✅)
- [x] Kanban dashboard with activity indicators
- [x] Root Cause Analysis with scoring system
- [x] Impact Analysis with BFS and risk levels
- [x] Interactive Graph View with vis-network

---

## 🛡️ Phase 3: Governance & Agentic Guardrails (Q4 2026)

*Goal: Control AI execution and ensure system integrity.*

### Active Architecture Enforcement
Prevent AI from introducing technical debt or breaking system constraints:

- [ ] **Cypher Rule Engine:**
  - Rules encoded as Cypher queries
  - Blocking commits or tasks that violate design patterns
  - Circular dependency prevention at write time
  - Forbidden layer access (e.g., Layer A cannot touch Layer C)

- [ ] **Policy Enforcement Levels:**
  - `WARN` - Log violations but allow
  - `BLOCK` - Prevent operation, require override
  - `STRICT` - No overrides allowed

- [ ] **Self-Documenting Enforcement:**
  - Verify "Solution Summary" exists before closing
  - Verify "Modified Files" section is complete
  - Verify "Technical Debt Notes" documents tradeoffs
  - Block agent from closing if documentation incomplete

### Dynamic RBAC for Agents
Role-based access control with agent-specific roles:

- [ ] **Role Definitions:**
  ```
  JuniorAgent:
    - Can: Create issues, update own issues, read all
    - Cannot: Close issues, modify architecture, delete
    
  SeniorAgent:
    - Can: All JuniorAgent + close issues, modify components
    - Cannot: Delete projects, modify constraints
    
  SecurityAgent:
    - Can: All SeniorAgent + define rules, block operations
    - Cannot: Override audit logs
  ```

- [ ] **Permission Matrix:**
  - Fine-grained permissions on graph operations
  - Project-level access control
  - Time-limited credentials

### Token Budgeting System
Control AI costs and prevent infinite loops:

- [ ] **Cost Tracking:**
  - `estimated_cost`: Pre-execution token estimate
  - `actual_cost`: Post-execution actual usage
  - `budget_limit`: Per-project or per-agent threshold
  - `cost_alert`: Notification threshold

- [ ] **Budget Actions:**
  - Auto-pause when limit reached
  - Human approval for overruns
  - Cost attribution by issue/component
  - Historical cost analytics

### Bidirectional GitHub Synchronization (v0.8.0 ✅)
- [x] GitHub API Adapter (Hexagonal architecture)
- [x] Bidirectional Webhook Listener
- [x] Causal Mirroring (analysis as GitHub comments)
- [x] Offline-First Sync Engine with ConnectivityManager + SyncQueue
- [x] Label-to-Graph Mapping
- [x] WebhookSignatureValidator
- [x] MarkdownTransformer (GitHub-flavored Markdown)
- [x] SecretManager (secure PAT handling)
- [x] GitHubIssueMapper (UUID ↔ GitHub Issue numbers)

### Autonomous Operations
- [ ] **Self-Healing:** Integration with `socialseed-e2e` for automatic fix task generation
- [ ] **Swarm Coordination:** Multi-agent role management (Planner, Developer, Reviewer)
- [ ] **Transaction Boundaries:** ACID multi-operation commits in Neo4j

---

## 🚀 Phase 4: Global Ecosystem & Autonomous Execution (2027)

*Goal: Industry standardization and full supervised autonomy.*

### Model Context Protocol (MCP) Server
Native server for AI tools to consume graph context directly:

- [ ] **MCP Implementation:**
  - Standard MCP protocol compliance
  - Direct graph context access
  - Claude Desktop integration
  - Cursor integration
  - Custom AI assistants

- [ ] **Context Providers:**
  - Issue context
  - Dependency graph
  - Architectural rules
  - Historical decisions
  - Code-as-Graph data

### IDE Integration
Official extensions for popular editors:

- [ ] **VS Code Extension:**
  - Issue panel
  - Dependency viewer
  - Architecture validation
  - Inline error markers

- [ ] **Cursor/Windsurf Integration:**
  - Real-time suggestions
  - Context injection
  - Architecture enforcement

- [ ] **Features:**
  - One-click issue assignment
  - Automatic status updates
  - Inline dependency visualization
  - Architectural rule highlights

### Autonomous Git Operations
Full lifecycle management from Issue to PR:

- [ ] **Automated Workflow:**
  - Issue → Branch creation
  - Branch → Development
  - Development → PR creation
  - PR → Graph-verified approval
  - Approval → Merge

- [ ] **Graph-Verified Approvals:**
  - Architectural rule validation
  - Test pass verification
  - Dependency impact check
  - Security scan validation

### Project Master Config
Single YAML file defining entire system architecture:

- [ ] **Config Schema:**
  ```yaml
  architecture:
    layers:
      - name: Presentation
        can_access: [Application]
      - name: Application
        can_access: [Domain]
      - name: Domain
        can_access: [Infrastructure]
    
    forbidden_dependencies:
      - from: Presentation
        to: Infrastructure
    
    max_depth: 3
  
  agent_roles:
    junior:
      max_concurrent_issues: 2
      requires_approval_for: [close, delete]
  ```

### Enterprise Features
- [ ] **Multi-Tenant SaaS:** Advanced Neo4j Aura support for enterprise scale
- [ ] **Community Demos:** Production-ready boilerplate (E-commerce, SaaS API)
- [ ] **E2E Test Suite:** Complete end-to-end testing coverage

### Stable API v1
- [ ] Locked API contracts
- [ ] Strict SemVer versioning
- [ ] Deprecation policy
- [ ] Breaking change communication

---

## 📊 Test Coverage (v0.8.0)

| Area | Status | Notes |
|------|--------|-------|
| Unit Tests | ✅ 270+ passing | Entities, actions, API, CLI, Neo4j, scaffolder |
| Neo4j Integration | ✅ Working | All queries functional with graph storage |
| CLI Functional | ✅ Complete | All commands tested with mock repositories |
| API Functional | ✅ Complete | All endpoints via TestClient |
| Integration Tests | ⚠️ 12/14 | Requires credential adjustments |
| E2E | ❌ Pending | Not implemented |

---

## 🔍 Known Issues Audit

| # | Issue | Severity | Status |
|---|-------|----------|--------|
| 1-20 | Various bug fixes (short UUID, pagination, etc.) | Low-Medium | ✅ RESOLVED |
| 21 | CLI blank lines (Typer/Rich) | Low | ⚠️ KNOWN LIMITATION |
| 22 | Architectural rules not enforced at write time | Medium | ✅ RESOLVED (v0.8.0) |

---

## 📋 Known Limitations

### CLI Blank Lines
CLI output (`tasker --help`, `tasker issue list`, etc.) shows extra blank lines at the start. Known Typer + Rich integration issue with no current workaround.

**Status:** Unresolved - Known limitation  
**Impact:** Low - Only affects visual presentation  
**Workaround:** None available

---

## 🎯 Version Roadmap

### v0.8.1 (Q2 2026) ✅
- Lint cleanup and code quality (Ruff config migration, variable naming fixes)
- Enhanced API documentation (OpenAPI descriptions, endpoint examples)
- CLI output polish (improved error messages)
- Performance optimization (monitoring middleware, Neo4j indexes, BFS query)
- Security enhancements (SECURITY.md, dependency-update workflow, pip-audit)
- Test coverage enhancement (454 tests, new AI/RAG tests)

### v0.9.0 - "Memory & Intelligence" (Q3 2026)
- Code-as-Graph with Tree-sitter
- RAG Native with vector indexes in Neo4j
- AI Reasoning Logs integrated in graph
- Enhanced impact analysis

### v1.0.0 - "The Architect" (2027)
- Native MCP Server
- Strict Guardrails (block operations violating architecture)
- Token budget management
- Stable API v1 (strict SemVer)
- IDE integrations (VS Code, Cursor, Windsurf)
- Autonomous Git Operations
- Complete E2E Test Suite

---

## 📄 Previous Releases

| Version | Date | Focus |
|---------|------|-------|
| 0.1.0 | 2024-02 | Initial structure |
| 0.2.0 | 2024-04 | Graph base |
| 0.3.0 | 2024-06 | CLI + API |
| 0.4.0 | 2024-08 | Analysis |
| 0.5.0 | 2025-01-15 | **Graph-Only** - Neo4j exclusive storage |
| 0.5.1 | 2026-04-07 | Post-Release Updates |
| 0.6.0 | 2026-04-08 | Polish & Alignment |
| 0.7.0 | 2025-10 | GitHub Integration |
| **0.8.0** | **2026-04-23** | **Observability & Active Governance** |

---

## 💡 CTO Implementation Notes

### Critical Considerations for Phase 2-4:

1. **Atomicity:** All graph updates by agents must be treated as ACID transactions. If architecture validation fails, the change must not persist.

2. **Sanitization:** The RAG system must filter secrets and API keys before generating embeddings to prevent data leaks to LLMs. Never store raw credentials in vector indexes.

3. **Synchronization:** The `WebhookSignatureValidator` implementation is critical for secure and reliable GitHub sync in production environments.

4. **Setup Friction:** Default to Neo4j local with sensible env vars as the happy path. The `docker-compose.yml` must work out-of-the-box for new users.

5. **Agent Trust Levels:** Different agent roles require different trust levels. JuniorAgents need more enforcement; SeniorAgents can override with justification.

---

**Building the future of software engineering, one node at a time.** 🛡️🕸️