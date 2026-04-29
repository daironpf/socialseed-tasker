# Workflow: Real-Test Evaluation (PyPI)

## Trigger Command
`prueba el proyecto pypi` or `test project from pypi`

## Description
Ejecuta una evaluación black-box completa del sistema SocialSeed Tasker instalando desde **PyPI** en lugar de código local. Este workflow simula cómo un usuario real experimentaría el proyecto después de instalarlo con `pip install socialseed-tasker`.

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
- `pip install socialseed-tasker` (install from PyPI)
- `docker-compose up/down` (infra)
- Archivos generados por `tasker init` en `real-test/`

---

## Phase 0: Requirements Capture

### Input
- **Use Case Description**: e.g., "Dental clinic appointment system"
- **Number of Issues**: e.g., 50 issues

### Process
1. Ask user for use case description
2. Ask user for number of issues to generate
3. Assign random profile from Section 0:
   - **Junior Dev**: Focus on documentation clarity, "Doc Gaps"
   - **Senior Architect**: Focus on graph efficiency, design patterns, scalability
   - **DevOps**: Focus on infrastructure, logs, response times, Docker stability
   - **Chaos Monkey**: Ignores documentation, uses only `--help` and error messages

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

4. **Install package from PyPI**:
   ```bash
   pip install socialseed-tasker
   ```

   > **IMPORTANT**: This is the key difference from local testing. We're testing what users get from PyPI.

5. **Verify installation**:
   ```bash
   tasker --version
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
   # Copy from main project (if available) or use scaffold
   # For pure PyPI test, the scaffold is sufficient
   ```

3. **Start services**:
   ```bash
   cd tasker && docker-compose up -d
   ```

4. **Wait for services to be ready**:
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
1. Launch Sub-Agent with assigned profile
2. Sub-Agent reads documentation from `real-test/docs/` or `real-test/.agent/`
3. Sub-Agent creates issues via REST API (NOT CLI - to test API)
4. Sub-Agent verifies issue count via GET endpoint
5. If discrepancy found: mark as FINDING with severity HIGH

---

## Phase 4: Report Generation

### Output: `real-test/report.md`

Must include:
- **Test Metadata**: date, version, use case, requested vs created issues
- **Installation Source**: **PyPI** (not local)
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
│ Services Running (DO NOT CLEANUP)                       │
├─────────────────────────────────────────────────────────┤
│ Neo4j Browser:  http://localhost:7474                   │
│   User: neo4j / neoSocial                               │
│                                                         │
│ API:        http://localhost:8000                       │
│   Docs:     http://localhost:8000/docs                  │
│                                                         │
│ Frontend:   http://localhost:8080                       │
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
  installation_source: "PyPI"  # <-- Key difference

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
  pypi_installation_score: 1-10  # <-- New metric for PyPI
  agent_friction_points: []
```

---

## Key Differences: PyPI vs Local

| Aspect | Local (`pip install -e .`) | PyPI (`pip install socialseed-tasker`) |
|--------|---------------------------|---------------------------------------|
| Source code | Available | Not available |
| Version | Current dev | Published release |
| Dependencies | From pyproject.toml | From PyPI metadata |
| Editable | Yes | No |
| User experience | Developer | End user |

---

## Workflow Execution

```
prueba el proyecto pypi
  → Phase 0: Ask use case + issue count
  → Phase 1: Setup real-test/ + venv + pip install from PyPI
  → Phase 2: tasker init + docker up
  → Phase 3: Create issues via API
  → Phase 4: Generate report.md
  → ⚠️ ASK: Cleanup or keep running?
  → WAIT for user response before acting
```

---

## Checklist

- [ ] Phase 0: Use case captured
- [ ] Phase 0: Issue count defined
- [ ] Phase 0: Profile assigned
- [ ] Phase 1: Containers stopped
- [ ] Phase 1: real-test/ created
- [ ] Phase 1: venv created and activated
- [ ] Phase 1: Package installed from **PyPI**
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