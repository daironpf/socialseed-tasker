# Workflow: Real-Test Evaluation

## Trigger Command
`test the project`

## Description
Executes a complete black-box evaluation of the SocialSeed Tasker system. This workflow simulates a real use case by creating issues in an isolated environment (real-test/) and evaluates system robustness from a Project Manager's perspective.

---

## ⚠️ INVIOLABLE RULE: Black-Box Restriction

> **UNDER NO CIRCUMSTANCES** are you allowed to access the source code in `src/` during this evaluation.
> If something fails, document it as a FINDING and continue. DO NOT look into the source code.

### Si No Puedes Continuar
1. Documenta el bloque como **FINDING** en `report.md`
2. Completa las fases restantes como "FAIL" o "N/A"
3. Genera el reporte final
4. Detén la ejecución

### Ejemplos de Violación (MUY GRAVE)
- Leer archivos en `src/` para entender cómo funciona algo
- Copiar configuraciones de `docker-compose.yml` del proyecto principal
- Buscar en código para encontrar endpoints o comandos

### Comandos Permitidos
- `tasker --help` (CLI help)
- `tasker init` (scaffold)
- `docker-compose up/down` (infra)
- Archivos generados por `tasker init` en `real-test/`

---

## Phase 0: Requirements Capture

### Input
- **Use Case Description**: e.g., "Dental clinic appointment system"
- **Number of Issues**: e.g., 50 issues
- **Issue Type**: Real issues with dependencies vs simple enumerated issues
- **Architecture Type**: Monolithic / Microservices / Serverless / API-first
- **Implementation Count**: Number of issues to implement (0 to 30) to test doc-sync and registry.

- **Quality Guide**: Optional reference for real issues at `skills/issue_quality_guide.json`

### Process
1. Ask user for use case description
2. Ask user for number of issues to generate
3. Ask user for issue type:
   - **Real Issues**: Issues with meaningful titles, descriptions, dependencies (uses quality guide)
   - **Simple Enumerated**: Task 1, Task 2, etc. (quick test)
4. Ask user for architecture type:
   - **Monolithic**: Single deployable unit (e.g., Django, Rails, Laravel)
   - **Microservices**: Independent services communicating via API (e.g., Go services, Node services)
   - **Serverless**: Function-based deployment (e.g., AWS Lambda, Cloud Functions)
   - **API-first**: Backend API with separate frontend (e.g., REST/GraphQL API + SPA)
5. Ask user for implementation count (0-30):
   - **None (0)**: Only test issue creation and graph storage.
   - **Partial (1-10)**: Test basic doc-sync and registry reflection.
   - **Stress (11-30)**: Test performance of documentation updates and registry consistency.
6. (Optional) Assign random profile from Section 0:
   - **Junior Dev**: Focus on documentation clarity, "Doc Gaps"
   - **Senior Architect**: Focus on graph efficiency, design patterns, scalability
   - **DevOps**: Focus on infrastructure, logs, response times, Docker stability
   - **Chaos Monkey**: Ignores documentation, uses only `--help` and error messages

### Issue Type Guide

| Option | Description | Tokens | Use Case |
|--------|-------------|--------|----------|
| Real Issues | Meaningful titles, descriptions, real dependencies | High | Test AI reasoning, graph complexity |
| Simple Enumerated | "Task 1", "Task 2", simple dependencies | Low | Quick API testing, basic functionality |

**Recommendation**: Use Simple Enumerated for quick tests (saves tokens). Use Real Issues for comprehensive testing.

---

## Phase 1: Environment Isolation

### Process
1. **Stop previous containers**:
   ```bash
   cd real-test && docker-compose down -v --remove-orphans
   ```

2. **Create isolation directory**:
   ```bash
   mkdir -p real-test && cd real-test
   ```

3. **Create and activate Python venv**:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # Windows
   # or: source venv/bin/activate  # Linux/Mac
   ```

4. **Install package in editable mode**:
   ```bash
   pip install -e ..
   # or: pip install .
   ```

---

## Phase 2: Infrastructure Initialization

### Process
1. **Run tasker init**:
   ```bash
   tasker init .
   ```

2. **Copy full frontend** (IMPORTANT! - scaffold is just placeholder):
   ```bash
   # Copy from main project
   cp -r ../../frontend/dist/* tasker/frontend/
   cp ../../frontend/nginx.conf tasker/frontend/
   ```

3. **Update Dockerfile** for full frontend:
   ```bash
   # Edit tasker/frontend/Dockerfile to:
   FROM nginx:alpine
   COPY index.html /usr/share/nginx/html/index.html
   COPY assets/ /usr/share/nginx/html/assets/
   COPY nginx.conf /etc/nginx/conf.d/default.conf
   EXPOSE 80
   CMD ["nginx", "-g", "daemon off;"]
   ```

4. **Start services** (with --no-cache first time):
   ```bash
   cd tasker && docker-compose build --no-cache tasker-board
   docker-compose up -d
   ```

5. **Wait for services to be ready**:
   ```bash
   sleep 10
   # Verify: docker-compose ps
   ```

---

## Phase 3: Agent Evaluation (Black Box)

### Sub-Agent Configuration
- **Role**: Project Manager / Architect
- **Mission**: Define issue architecture (user stories, technical tasks, dependencies) for the given use case
- **Constraint**: MUST NOT write any code. Success is measured by creating issues in the Tasker graph.

### Assigned Profile Behavior
| Profile | Behavior |
|---------|----------|
| Junior Dev | Relies heavily on step-by-step documentation |
| Senior Architect | Focuses on graph efficiency and design patterns |
| DevOps | Focuses on infrastructure and Docker stability |
| Chaos Monkey | Uses ONLY `tasker --help` and error messages. NO documentation reading |

### Process

**For Simple Enumerated Issues** (default - quick test):
1. Create component with use case name
2. Create N issues with simple titles: "Task 1: [Use Case] feature", "Task 2: [Use Case] feature", etc.
3. Create simple dependencies (5-10% of issues)
4. Verify via API

**For Real Issues** (requires AI reasoning):
1. Launch Sub-Agent with assigned profile
2. Sub-Agent reads:
   - `skills/issue_quality_guide.json` (quality standards)
   - Documentation from `real-test/docs/` or `real-test/.agent/`
3. Sub-Agent creates issues following quality guide standards:
   - Titles follow pattern: [Component] Action: Expected Result
   - Descriptions include Context, Acceptance Criteria, Technical Notes
   - Priority matches guide (CRITICAL/HIGH/MEDIUM/LOW)
4. Sub-Agent creates dependencies between issues (10-15%):
   - Link high-priority issues to their prerequisites
   - Create dependency chains
   - Use add_dependency() for all relationships
5. Sub-Agent verifies:
   - Issue count via GET endpoint
   - Dependency creation via GET /api/v1/issues/{id}/dependencies

6. If discrepancy found: mark as FINDING with severity HIGH

### Test Dependencies (Simple Enumerated)
Quick script to create simple dependencies:
```bash
# For 50 issues, create 5 simple dependencies
# Issue N depends on Issue N-1 (linear chain)
for i in {2..6}; do
  curl -X POST "http://localhost:8000/api/v1/issues/$ID_$i/dependencies" \
    -H "Content-Type: application/json" \
    -d '{"depends_on_id": "$ID_$((i-1))"}'
done
```

---

## Phase 4: Implementation & Doc-Sync Behavior Analysis

### ⚠️ REQUIRED SKILLS for Phase 4

**BEFORE starting Phase 4**, the agent MUST load these skills in order:

1. **`.agent/skills/programming-agent-governance.md`** (PRIMARY)
   - Issue resolution workflow
   - Policy compliance
   - Breaking changes prevention
   
2. **`.agent/skills/code-as-graph-analysis.md`** (GRAPH AWARENESS)
   - Graph relationship queries
   - Impact analysis (CodeSymbol CALLS)
   - Causal traceability
   
3. **`.agent/skills/documentation-sync.md`**
   - Doc sync rules
   
4. **`.agent/skills/hexagonal-architecture.md`**
   - Architecture constraints

### Graph Relationships for Issue Resolution

The agent MUST leverage these graph relationships as defined in `GraphDataModelDetails.md`:

| Relationship | Description | Used When |
|--------------|-------------|-----------|
| `(Project)-[:HAS_ISSUE]->(Issue)` | Issue belongs to project | Create/assign issue |
| `(Issue)-[:PART_OF]->(Component)` | Issue linked to component | Check scope |
| `(Issue)-[:DEPENDS_ON]->(Issue)` | Issue dependencies | Verify closed before work |
| `(Issue)-[:RESOLVED_BY]->(Commit)` | Issue solved by commit | Close issue with commit |
| `(Agent)-[:PRODUCED]->(ReasoningNode)` | Agent reasoning trace | Add reasoning log |
| `(Agent)-[:MUST_COMPLY_WITH]->(Policy)` | Policy enforcement | Check before changes |
| `(Issue)-[:AFFECTS]->(CodeSymbol)` | Code impacted | Impact analysis |
| `(CodeSymbol)-[:CALLS]->(CodeSymbol)` | Method dependencies | Find affected code |

### Objective
Observe and validate the agent's ability to solve technical issues and keep project documentation synchronized, following the specific rules defined in:
- `.agent/skills/documentation-sync.md`
- `.agent/skills/hexagonal-architecture.md`
- `.agent/skills/programming-agent-governance.md` (REQUIRED)
- `.agent/skills/code-as-graph-analysis.md` (REQUIRED)

### Process for Agent Implementation
For a subset of issues (defined in Phase 0), the agent MUST:

1.  **Analyze Context** (Graph-Aware):
    -   Read the issue details from the API or `.issues/` folder.
    -   Query graph for component context: `GET /api/v1/components/{id}`
    -   Query graph for policies: `GET /api/v1/policies?component={id}`
    -   Consult the `real-test/.agent/skills/` to understand the specific conventions.
2.  **Execute Technical Implementation**:
    -   Perform impact analysis before modifying code
    -   Create or modify source files in `real-test/src/`.
    -   The code must reflect the requested feature/fix and adhere to the project's architectural constraints.
3.  **Perform Documentation Sync (CRITICAL)**:
    -   **ROADMAP.md**: Update the "Last updated" date and mark the issue as RESOLVED in the Known Issues table.
    -   **VERSIONS.md**: Add a checkmark `[x]` to the corresponding entry in the version checklist.
    -   **README.md**: If the implementation adds a new CLI command or environment variable, update the "Quick Start" or "Configuration" sections.
    -   **API_REFERENCE.md**: Update if a new endpoint was added.
4.  **Verification**:
    -   Ensure the implementation is correctly registered in the system (e.g., closing the issue via API with a detailed reasoning log).
    -   Verify that documentation changes are consistent and do not break the formatting of the files.

### Audit Criteria for Agent Behavior
- **Adherence**: Did the agent follow `documentation-sync.md`?
- **Integration**: Is the code consistent with the documentation updates?
- **Reasoning**: Do the reasoning logs in the API reflect the actual technical decisions made?
- **Self-Correction**: If the agent detects a doc gap while implementing, does it fix it?
- **Governance**: Did the agent follow `programming-agent-governance.md`? (REQUIRED)
  - Used Tasker API endpoints for documentation?
  - Checked policies before implementation?
  - Added reasoning log on close?
  - Updated ROADMAP.md and VERSIONS.md?
- **Graph Awareness**: Did the agent follow `code-as-graph-analysis.md`? (REQUIRED)
  - Queried component context from graph?
  - Performed impact analysis before code changes?
  - Linked CodeSymbols to issue in reasoning log?
  - Verified no policy violations?


---

## Phase 5: Report Generation

### Output: `real-test/report.md`

Must include:
- **Test Metadata**: date, version, use case, requested vs created issues, implementation count, successful implementations.
- **Findings**:
  - DOC_GAP: Documentation inconsistencies
  - DOC_SYNC_FAILURE: Errors during automatic doc updates (Phase 4)
  - REGISTRY_DESYNC: Implementation registry not reflected correctly (Phase 4)
  - BUG: Code bugs
  - REFACTOR: Technical debt suggestions
  - FEATURE_REQ: Missing features
- **DX Evaluation Scores** (1-10):
  - cli_intuition_score
  - error_message_clarity
  - documentation_score
  - api_clarity
  - setup_friction
  - dependency_graph_score: Ability to create and query dependencies

### ⚠️ ASK BEFORE CLEANUP

**YOU MUST ASK THE USER BEFORE CLEANUP** using the Question tool:

Question: "Do you want to cleanup services (docker-compose down) or keep them running to continue testing?"

| Options | Action |
|--------|--------|
| **Limpiar / Cleanup / NO** | Execute cleanup commands |
| **Mantener / Keep / YES** | Keep services running, provide access info |
| **Otra cosa** | Ask what they need |

**IMPORTANT**: 
- NEVER cleanup without explicit confirmation
- If user doesn't answer clearly, ask again
- Default is to NOT cleanup (wait for user response)

### If YES (Keep Services Running)

**Do NOT cleanup.** Provide access information:
```
┌─────────────────────────────────────────────────────────┐
│ Services Running (DO NOT CLEANUP)                          │
├─────────────────────────────────────────────────────────┤
│ Neo4j Browser:  http://localhost:7474                    │
│   User: neo4j / neoSocial                            │
│                                                         │
│ API:        http://localhost:8000                     │
│   Docs:     http://localhost:8000/docs                 │
│                                                         │
│ Frontend:   http://localhost:8080                     │
└─────────────────────────────────────────────────────────┘
```

**Commands you can run now:**
```bash
# Ver issues via API
curl http://localhost:8000/api/v1/issues

# Ver issues via CLI (in real-test/)
cd real-test && ./venv/Scripts/tasker.exe issue list

# Ver componentes
curl http://localhost:8000/api/v1/components

# Ver Neo4j data (cypher-shell)
docker exec -it tasker-db cypher-shell -u neo4j -p neoSocial

# When done later, run:
cd real-test/tasker && docker-compose down -v --remove-orphans
```

### If NO (Cleanup) or User Confirms Cleanup

**Only if user explicitly confirms "cleanup" or "limpiar"**:
```bash
# Stop containers: docker-compose down -v --remove-orphans
# Deactivate venv: deactivate
# Leave system ready for next iteration
```

**IMPORTANT**: Wait for user confirmation before running cleanup commands.

---

## Profile Descriptions

### Junior Dev
- Reports: Documentation gaps, unclear tutorials
- Actions: Seeks step-by-step guides, asks for clarification

### Senior Architect
- Reports: Graph efficiency issues, design patterns violations, scalability concerns
- Actions: Analyzes dependency chains, suggests refactoring

### DevOps
- Reports: Infrastructure issues, slow response times, Docker problems
- Actions: Checks logs, monitors containers, measures performance

### Chaos Monkey (User without Context)
- **PROHIBITION**: Cannot read docs/ or .agent/ files
- **ALLOWED**: Only `tasker --help` and terminal error messages
- Reports: How intuitive the tool is, error message helpfulness
- Actions: Trial and error based on CLI feedback

---

## YAML Schema for Findings

```yaml
test_metadata:
  date: "YYYY-MM-DD"
  target_version: "0.9.0"
  use_case: "Description"
  requested_issues: 50
  created_issues: 0
  success_rate: "0%"

findings:
  - id: "FIND-001"
    type: "BUG | DOC_GAP | REFACTOR | FEATURE_REQ"
    component: "CLI | API | CORE | DOCKER | GRAPH_ENGINE"
    severity: "CRITICAL | HIGH | MEDIUM | LOW"
    title: "Concise title"
    description: "Technical explanation"
    evidence:
      log_trace: "Exact error"
      missing_info: "What was unclear"
    suggested_fix: "Technical proposal"
    impact: "How it affects autonomy"
    reproduction_steps:
      - "Command: ..."
      - "Payload: ..."
      - "Response: ..."

dx_evaluation:
  cli_intuition_score: 1-10
  error_message_clarity: 1-10
  documentation_score: 1-10
  api_clarity: 1-10
  setup_friction: 1-10
  agent_friction_points: []
```

## Workflow Execution

```
test the project
  → Phase 0: Ask use case + issue count + issue type + architecture + implementation count
  → Phase 1: Setup real-test/ + venv
  → Phase 2: tasker init + docker up
  → Phase 3: Create issues via API (simple or real)
  → Phase 4: Implementation & Doc Sync Evaluation (0-30 issues)
  → Phase 5: Generate report.md
  → ⚠️ ASK: Cleanup or keep running?
  → WAIT for user response before acting
```

## Checklist

- [ ] Phase 0: Use case captured
- [ ] Phase 0: Issue count defined
- [ ] Phase 0: Issue type defined (real vs simple)
- [ ] Phase 0: Architecture type defined
- [ ] Phase 0: Profile assigned
- [ ] Phase 1: Containers stopped
- [ ] Phase 1: real-test/ created
- [ ] Phase 1: venv created and activated
- [ ] Phase 1: Package installed
- [ ] Phase 2: tasker init executed
- [ ] Phase 2: Docker services up
- [ ] Phase 3: Documentation available
- [ ] Phase 3: Issues created via API
- [ ] Phase 3: Issue count verified
- [ ] Phase 4: Implementation subset selected (0-30)
- [ ] Phase 4: Doc-sync performed and verified
- [ ] Phase 4: Registry reflection verified (Logs/DB)
- [ ] Phase 5: report.md generated
- [ ] Phase 5: ASK user for cleanup decision ⚠️
- [ ] Phase 5: Cleanup (only if user confirmed)

## Manual Cleanup (When User Confirms)

**IMPORTANT**: Only run cleanup if user explicitly asks for it.

```bash
# Clean Docker + volumes
cd real-test/tasker && docker-compose down -v --remove-orphans

# Or just stop (data persists)
cd real-test/tasker && docker-compose down

# Deactivate venv (from real-test/)
deactivate
```