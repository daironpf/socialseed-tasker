# Workflow: Real-Test Evaluation

## Trigger Command
`test the project`

## Description
Executes a complete black-box evaluation of the SocialSeed Tasker system. This workflow simulates a real use case by creating issues in an isolated environment (`real-test/`) and evaluates system robustness from a Project Manager's perspective.

---

## Table of Contents
- [Inviolable Rule](#-inviolable-rule-black-box-restriction)
- [Phase 0: Requirements Capture](#phase-0-requirements-capture)
- [Phase 1: Environment Isolation](#phase-1-environment-isolation)
- [Phase 2: Infrastructure Initialization](#phase-2-infrastructure-initialization)
- [Phase 3: Issue Creation (Black Box)](#phase-3-issue-creation-black-box)
- [Phase 4: Implementation & Doc-Sync](#phase-4-implementation--doc-sync-behavior-analysis)
- [Phase 5: Report Generation](#phase-5-report-generation)
- [Cleanup](#cleanup)

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
- `tasker --help`, `tasker install`, `tasker init` (CLI de instalación)
- `tasker component create/list/show/delete` (componentes)
- `tasker issue create/list/show/close` (issues)
- `tasker dependency add/list/chain/blocked` (dependencias)
- `tasker serve`, `tasker restart` (servidor)
- `docker compose up/down` (infra)
- `curl` para consultar API
- Archivos generados por `tasker install`/`tasker init` en `real-test/`

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
6. (Optional) Assign random profile from the profile table below:
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

## Phase 1: Simular Instalación de Usuario

Simula la experiencia de un usuario que instala SocialSeed Tasker por primera vez.

### Process
0. **Create `real-test/` directory if it doesn't exist**:
   ```bash
   mkdir -p real-test
   ```

1. **Stop previous containers** (if any):
   ```bash
   cd real-test 2>/dev/null && docker compose --profile full down -v --remove-orphans && cd ..
   rm -rf real-test
   ```

2. **Create clean project directory** (simula el proyecto del usuario):
   ```bash
   mkdir -p real-test && cd real-test

# If real-test/ already exists and you want to start fresh, delete it first:
# rm -rf real-test && mkdir -p real-test && cd real-test
   git init
   ```

3. **Create and activate Python venv**:
   ```bash
   python -m venv venv
   # Windows:
   source venv/Scripts/activate
   # Linux/Mac:
   # source venv/bin/activate
   ```

4. **Install package** (como un usuario real desde PyPI):
   ```bash
   pip install socialseed-tasker
   ```
   > Si el paquete no está publicado, instalar desde el repo local:
   > `pip install -e ..`

---

## Phase 2: Scaffolding e Inicialización

Simula los comandos que ejecuta un usuario tras instalar el paquete.

### Process
1. **Scaffold Tasker en el proyecto** (`tasker install`):
   ```bash
   tasker install .
   ```
   > 📌 Crea `.agent/` con skills, workflows, docker-compose, configs.

2. **Inicializar y arrancar todo** (`tasker init`):
   ```bash
   tasker init
   ```
   > `tasker init` guía al usuario interactivamente: nombre del proyecto, tecnología, etc.

   Durante la inicialización interactiva, debes responder las preguntas del menú de la siguiente manera:

   a. En el menú de opciones (1-8), selecciona directamente **START** presionando Enter.
   b. Cuando pregunte por el Project Name, ingresa el nombre del use case.
   c. Cuando pregunte por el **Connection Mode**, selecciona la opción **``2) API (REST)``**.
   d. Para el resto de opciones acepta los valores por defecto.

   > **Al finalizar, automáticamente levanta docker compose con el profile ``api``, crea el proyecto en Neo4j,
   > y deja el sistema listo para usar.** No requiere pasos adicionales.

3. **Verificar que el sistema está listo**:
   ```bash
   tasker status
   ```

4. **Verificar archivos generados**:
   ```bash
   ls -la .agent/tasker/
   ```

5. **Inicializar git y commit inicial** (como haría un usuario real):
   ```bash
   git add -A && git commit -m "chore: initial tasker scaffold"
   ```

---

## Phase 3: Interacción como Usuario Real (Black Box)

Evalúa el sistema desde la perspectiva de un usuario que interactúa **exclusivamente a través de la CLI** y la API REST, sin acceso al código fuente.

### Sub-Agent Configuration
- **Role**: Project Manager / Product Owner
- **Mission**: Gestionar el proyecto usando únicamente los comandos CLI y endpoints API documentados
- **Constraint**: MUST NOT leer `src/`. Solo usa `--help`, documentación generada, y respuestas del servidor.

### Assigned Profile Behavior
| Profile | Behavior |
|---------|----------|
| Junior Dev | Usa `--help` extensivamente, sigue la documentación al pie de la letra |
| Senior Architect | Prueba features avanzadas: dependencias, análisis de impacto, RAG |
| DevOps | Prueba docker, health checks, logs, restart del servidor |
| Chaos Monkey | Solo usa `tasker --help` and mensajes de error. NO lee documentación |

### Proceso General (ambos tipos de issues)

**Siempre usando la CLI (desde `real-test/` con venv activado):**

#### A. Exploración Inicial
```bash
# El usuario explora el CLI
tasker --help
tasker component --help
tasker issue --help

# Listar componentes (debería estar vacío o con default)
tasker component list
```

#### B. Gestión de Componentes
```bash
# Crear componente para el use case
tasker component create <use-case-slug> --project "test"

# Verificar
tasker component list
tasker component show <component-id>
```

#### C. Creación de Issues vía CLI
```bash
# Crear issues como un usuario real
tasker issue create "Task 1: <use case> feature" --component <component-id> --priority HIGH
tasker issue create "Task 2: <use case> feature" --component <component-id> --priority MEDIUM

# Verificar
tasker issue list
tasker issue show <issue-id>
```

#### D. Gestión de Dependencias vía CLI
```bash
# Crear dependencias entre issues
tasker dependency add <issue-2-id> --depends-on <issue-1-id>

# Verificar cadena de dependencias
tasker dependency chain <issue-2-id>
tasker dependency blocked
```

#### E. Operaciones Avanzadas vía CLI
```bash
# Marcar issue como en progreso
tasker issue start <issue-id>

# Cerrar issue
tasker issue close <issue-id>

# Ver estado del servidor
tasker status
```

#### F. Pruebas de Estrés y Límites (Robustez de Grafo)
```bash
# Intentar crear dependencias circulares (debe fallar elegantemente)
tasker dependency add <issue-1-id> --depends-on <issue-2-id>
# Nota: Verificar que la CLI detecte el ciclo y aborte con un mensaje claro y exit code != 0.

# Prueba de carga (Crear una cadena lineal larga de más de 20 dependencias)
# Verificar tiempos de respuesta de comandos de consulta de árbol como:
tasker dependency chain <issue-n-id>
```

#### G. Inyección de Fallas (Chaos & Resiliencia)
```bash
# 1. Simular caída de base de datos Neo4j
cd real-test && docker compose stop tasker-db && cd ..

# 2. Ejecutar comando CLI y verificar manejo de excepciones
cd real-test && tasker issue list
# Nota: La CLI debe fallar con gracia, mostrando un error amigable de conexión en lugar de un traceback de Python.
# Confirmar que el exit code de la CLI sea diferente de 0.

# 3. Restaurar servicio
cd real-test && docker compose start tasker-db && cd ..
```

#### H. Verificaciones DX y Códigos de Retorno
*   **Códigos de Salida:** Verificar explícitamente que cada comando fallido retorne un código de estado de salida distinto de `0` (ej: `$LASTEXITCODE` en PowerShell o `$?` en Bash).
*   **Formato de Errores:** Validar que los errores de la CLI utilicen un esquema estructurado (ej. `[ERROR]: <mensaje_amigable>`) y no expongan rutas absolutas locales ni credenciales internas de Neo4j en la salida estándar.

#### I. Portabilidad de Rutas en Windows/Unix
*   **Normalización de Paths:** Comprobar que todos los paths almacenados en el grafo o en los archivos de configuración `.agent/` utilicen diagonales estandarizadas (`/`) y no contengan barras cruzadas (`\`) de Windows que puedan romper el comportamiento multiplataforma.

#### J. Integración con Git History e Integridad
*   **Vinculación de Commits:** Verificar que al cerrar un issue usando la CLI, se asocie el hash de commit correcto en el grafo y que los commits del historial del proyecto dummy en `real-test/` reflejen claramente el formato `[Issue-ID]`.

---

### For Simple Enumerated Issues (default - quick test)

1. Crear 1 componente con el nombre del use case
2. Crear N issues secuenciales vía CLI: `tasker issue create "Task N: ..." --component <id>`
3. Crear dependencias lineales (5-10%): `tasker dependency add <id2> --depends-on <id1>`
4. Verificar con: `tasker issue list` and `tasker dependency blocked`

### For Real Issues (comprehensive test)

1. Leer `skills/issue_quality_guide.json` para estándares de calidad
2. Crear issues con títulos y descripciones significativas usando la CLI
3. Crear dependencias realistas (10-15% de los issues)
4. Verificar con comandos CLI y endpoints API:
   - `tasker issue list` / `tasker issue show <id>`
   - `GET /api/v1/issues` / `GET /api/v1/issues/{id}/dependencies`
5. Si hay discrepancias: marcar como FINDING con severity HIGH

---
### Endpoints API para verificación adicional

```bash
# Verificar todo via API (como haría un integrador) — puerto 8888 en API mode
curl http://localhost:8888/api/v1/components | python -m json.tool
curl http://localhost:8888/api/v1/issues | python -m json.tool

# Ver detalle de issue
curl http://localhost:8888/api/v1/issues/<issue-id>

# Verificar salud del sistema
curl http://localhost:8888/health
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
Observe and validate the agent's ability to solve technical issues, execute programming tasks, and keep project documentation synchronized, following the specific rules defined in this workflow and the loaded skills.

---

### Developer Tutorial: How the Agent MUST use Tasker during Programming

When the agent is tasked to program a feature or fix a bug in `real-test/` (Phase 4), it MUST follow the rigorous development workflow powered by Tasker CLI and REST API:

#### 1. Context Analysis & Issue Fetching
Before writing code, read the assigned issue details to understand the scope and dependencies:
```bash
# Via CLI: Get issue details
tasker issue show <issue-id>

# Alternative REST API call:
curl http://localhost:8888/api/v1/issues/<issue-id>
```

#### 2. Dependency Checking
Ensure that no active blocked dependencies exist before starting the implementation:
```bash
# Via CLI: Check dependency chain
tasker dependency chain <issue-id>

# Alternative REST API:
curl http://localhost:8888/api/v1/issues/<issue-id>/dependency-chain
```
*   **Rule:** If any dependency is still in state `OPEN`, `IN_PROGRESS` or `BLOCKED`, the agent **must not** start writing code. It must resolve blocking issues first.

#### 3. Code-as-Graph Scan & Impact Analysis
Tasker uses CodeSymbol mapping to calculate downstream risks before changes are made. The agent must scan the codebase and query impact:
```bash
# 1. Scan codebase symbols into the graph
tasker code-graph scan src/

# 2. Analyze impact of modifying a specific code symbol (e.g., function or class name)
tasker code-graph impact <SymbolName>

# Alternative REST API:
curl http://localhost:8888/api/v1/analyze/impact/<issue-id>
```

#### 4. Policy & Constraints Consultation
Consult architectural and technological policies established in the project:
```bash
# List policies
tasker constraints list

# Alternative REST API:
curl http://localhost:8888/api/v1/constraints
```

#### 5. Code Implementation
Proceed to write/modify code under `real-test/src` (or target directory). Follow instructions and design specifications (e.g., hexagonal architecture boundaries).

#### 6. Policy Validation
Verify that code changes do not break constraints (e.g. imports restrictions, library bans):
```bash
# Validate codebase compliance
tasker constraints validate

# Alternative REST API:
curl -X POST http://localhost:8888/api/v1/constraints/validate
```

#### 7. Documentation Sync (Doc-Sync)
Every code change requires immediate, synchronous updates to documentation files to prevent documentation rot:
*   **ROADMAP.md:** Update status of the issue to `RESOLVED` in the Known Issues table.
*   **VERSIONS.md:** Tick the corresponding item in the checklist: `- [x] Issue <ID> implemented`.
*   **README.md:** Update "Quick Start" or commands section if CLI/variables changed.

#### 8. Log Reasoning (Traceability)
Store a decision trace in the Neo4j graph for future reference:
```bash
# Log thought trace to Tasker graph
tasker reasoning log --issue <issue-id> --thought "Implemented robust validation utilizing HSL color palettes and closed security gaps with regex filters. All tests passing."

# Alternative REST API:
curl -X POST http://localhost:8888/api/v1/reasoning/log \
  -H "Content-Type: application/json" \
  -d '{
    "context": "implementation",
    "reasoning": "Detailed technical justification here",
    "issue_id": "<issue-id>",
    "files_modified": ["src/validator.py"],
    "tests_passed": true
  }'
```

#### 9. Close Issue
Once everything is fully validated, mark the issue as closed in the registry:
```bash
# Close via CLI
tasker issue close <issue-id>

# Alternative REST API:
curl -X POST http://localhost:8888/api/v1/issues/<issue-id>/close
```

---

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
 │ API:        http://localhost:8888                     │
 │   Docs:     http://localhost:8888/docs                 │
│                                                         │
│ Frontend:   http://localhost:8080                     │
└─────────────────────────────────────────────────────────┘
```

**Commands you can run now:**
```bash
# Ver issues via API
curl http://localhost:8888/api/v1/issues

# Ver issues via CLI (in real-test/ with venv active)
cd real-test && tasker issue list

# Ver componentes
curl http://localhost:8888/api/v1/components

# Ver Neo4j data (cypher-shell)
docker exec -it tasker-db cypher-shell -u neo4j -p neoSocial

# When done later, run:
cd real-test && docker compose --profile api down -v --remove-orphans
```

### If NO (Cleanup) or User Confirms Cleanup

**Only if user explicitly confirms "cleanup" or "limpiar"**:
```bash
# Stop containers: docker compose down -v --remove-orphans
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
  target_version: "1.0.4"
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
  → Phase 1: pip install socialseed-tasker + git init
  → Phase 2: tasker install → tasker init (levanta todo automáticamente)
  → Phase 3: User interaction via CLI (component/issue/dependency commands)
             + Graph Stress & Cycle tests
             + Fault Injection & Chaos testing
             + Return Codes & Portability verification
  → Phase 4: Implementation & Doc Sync Evaluation (0-30 issues)
             + Git History verification
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
- [ ] Phase 1: Crear real-test/ (mkdir -p) si no existe
- [ ] Phase 1: Limpiar real-test/ anterior (opcional)
- [ ] Phase 1: git init en proyecto limpio
- [ ] Phase 1: venv creado y activado
- [ ] Phase 1: pip install socialseed-tasker
- [ ] Phase 2: tasker install ejecutado (scaffold)
- [ ] Phase 2: tasker init ejecutado (configuración con modo API)
- [ ] Phase 2: tasker init completado (docker con --profile api + proyecto creados automáticamente)
- [ ] Phase 2: tasker status responde OK
- [ ] Phase 3: Exploración inicial: tasker --help, tasker component list
- [ ] Phase 3: Componente creado vía CLI
- [ ] Phase 3: Issues creados vía CLI
- [ ] Phase 3: Dependencias creadas vía CLI
- [ ] Phase 3: Verificación de ciclo circular rechazada (Prueba de límites)
- [ ] Phase 3: Prueba de resiliencia ante parada de DB (Chaos Testing)
- [ ] Phase 3: Verificación de Exit Codes y formato de errores (DX)
- [ ] Phase 3: Comprobación de normalización de rutas (Portabilidad)
- [ ] Phase 3: Verificación via CLI and API
- [ ] Phase 4: Implementation subset selected (0-30)
- [ ] Phase 4: Doc-sync performed and verified
- [ ] Phase 4: Git history vinculación y consistencia verificada
- [ ] Phase 4: Registry reflection verified (Logs/DB)
- [ ] Phase 5: report.md generated con métricas objetivas de DX
- [ ] Phase 5: ASK user for cleanup decision ⚠️
- [ ] Phase 5: Cleanup (only if user confirmed)

## Manual Cleanup (When User Confirms)

**IMPORTANT**: Only run cleanup if user explicitly asks for it.

```bash
# Clean Docker + volumes
cd real-test && docker compose --profile full down -v --remove-orphans

# Or just stop (data persists)
cd real-test && docker compose --profile full down

# Deactivate venv (from real-test/)
deactivate
```

---

## Audio Notification

When workflow completes, execute:

```bash
# Windows (from project root, relative path)
python .agent/assets/play_audio.py ".agent/assets/audios/Prueba Completada.mp3"
```