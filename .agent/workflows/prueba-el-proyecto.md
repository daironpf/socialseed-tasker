# Workflow: Real-Test Evaluation

## Trigger Command
`prueba el proyecto`

## Description
Ejecuta una evaluación black-box completa del sistema SocialSeed Tasker. Este workflow simula un caso de uso real creando issues en un entorno aislado (real-test/) y evalúa la robustez del sistema desde la perspectiva de un Project Manager.

---

## ⚠️ REGLA INVIOBLE: Restricción de Caja Negra

> **BAJO NINGUNA CIRCUNSTANCIA** puedes acceder al código fuente en `src/` durante la ejecución de esta evaluación.
> Si algo falla, debes documentarlo como FINDING y continuar, NO buscar en el código fuente.

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

### Process
1. Ask user for use case description
2. Ask user for number of issues to generate
3. Ask user for issue type:
   - **Real Issues**: Issues with meaningful titles and descriptions, real dependencies that require AI reasoning
   - **Simple Enumerated**: Simple numbered issues ("Task 1", "Task 2") without complex dependencies
4. Assign random profile from Section 0:
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
2. Sub-Agent reads documentation from `real-test/docs/` or `real-test/.agent/
3. Sub-Agent creates issues via REST API with meaningful titles and descriptions
4. Sub-Agent creates dependencies between issues (10-15% of issues should have dependencies):
   - Link high-priority issues to their prerequisites
   - Create dependency chains
   - Test blocked/blocking relationships
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

## Phase 4: Report Generation

### Output: `real-test/report.md`

Must include:
- **Test Metadata**: date, version, use case, requested vs created issues, dependencies created
- **Findings**:
  - DOC_GAP: Documentation inconsistencies
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

Question: "¿Deseas limpiar los servicios (docker-compose down) o mantenerlos corriendo para continuar probando?"

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
  target_version: "0.8.0"
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

---

## Workflow Execution

```
prueba el proyecto
  → Phase 0: Ask use case + issue count + issue type
  → Phase 1: Setup real-test/ + venv
  → Phase 2: tasker init + docker up
  → Phase 3: Create issues via API (simple or real)
  → Phase 4: Generate report.md
  → ⚠️ ASK: Cleanup or keep running?
  → WAIT for user response before acting
```

## Checklist

- [ ] Phase 0: Use case captured
- [ ] Phase 0: Issue count defined
- [ ] Phase 0: Issue type defined (real vs simple)
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
- [ ] Phase 4: report.md generated
- [ ] Phase 4: ASK user for cleanup decision ⚠️
- [ ] Phase 4: Cleanup (only if user confirmed)

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