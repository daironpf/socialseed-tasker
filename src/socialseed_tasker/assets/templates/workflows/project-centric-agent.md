# Workflow: Project-Centric Agent Behavior

## Purpose
All AI agents working on this project must treat **Tasker** as the single source of truth for all project-related information and actions.

## Single Project Rule
**Tasker supports only ONE project per instance.** All issues, components, agents, and code symbols belong to this single project. When the user mentions "the project", they are referring to this single Tasker project.

---

## Rule: Always Check with Tasker First

When a user mentions anything related to the project (in English or Spanish), the agent MUST consult Tasker before taking any action.

### Trigger Keywords - Project Management (ES)
- proyecto, proyecto actual, mi proyecto, el proyecto
- tarea, tarea nueva, crear tarea, abrir tarea
- issue, incidencias, feature, bug, error, problema
- componente, módulo, arquitectura, layer
- estado, progreso, avance, dashboard

### Trigger Keywords - Project Management (EN)
- project, current project, my project, the project
- task, new task, create task, open task
- issue, feature, bug, error, problem
- component, module, architecture, layer
- status, progress, dashboard

### Trigger Keywords - Documentation (ES)
- documentación, docs, documentar, readme
- changelog, historia, guías, manual
- spec, especificaciones, requisitos

### Trigger Keywords - Documentation (EN)
- documentation, docs, document, readme
- changelog, history, guides, manual
- spec, specifications, requirements

### Trigger Keywords - Code & Analysis (ES)
- código, refactorizar, analizar, dependencia
- test, pruebas, testing, coverage
- símbolo, import, clase, método, función

### Trigger Keywords - Code & Analysis (EN)
- code, refactor, analyze, dependency
- test, testing, coverage
- symbol, import, class, method, function

### Trigger Keywords - Agents & Team (ES)
- agente, desarrolladores, testers, equipo
- asignación, especializarse, capacidad

### Trigger Keywords - Agents & Team (EN)
- agent, developers, testers, team
- assignment, specialize, capability

---

## Workflow

### Step 1: Detect Project Context
When the user mentions project-related keywords, the agent must:

```bash
# Get current project info
curl http://localhost:8000/api/v1/projects/current

# Check if agent is registered
curl http://localhost:8000/api/v1/agents
```

### Step 2: Query Tasker for Relevant Information
Based on what the user asks, query the appropriate endpoint:

| User Request | Tasker Action |
|---|---|
| "What's the project status?" | `GET /projects/current` |
| "Show me the issues" | `GET /api/v1/issues?status=OPEN` |
| "Create a new task" | `POST /api/v1/issues` |
| "Update issue status" | `PATCH /api/v1/issues/{id}` |
| "Close issue" | `POST /api/v1/issues/{id}/close` |
| "What components exist?" | `GET /api/v1/components` |
| "Create component" | `POST /api/v1/components` |
| "Show me agents" | `GET /api/v1/agents` |
| "Register agent" | `POST /api/v1/agents/register` |
| "Add reasoning" | `POST /api/v1/reasoning/log` |
| "Search knowledge" | `GET /api/v1/rag/search` |
| "Code impact analysis" | `POST /api/v1/code-graph/impact` |
| "Update documentation" | Use `tasker documentation sync` |

### Step 3: If Functionality Not Available
If the requested action is not implemented in Tasker:

1. **Notify the user clearly**:
   ```
   "The action you're requesting is not yet implemented in Tasker.
   Current Tasker API supports:
   - Issue management (create, list, update, close)
   - Component tracking
   - Agent registration and specialization
   - Code graph analysis
   - RAG-based knowledge search
   - Reasoning/logging for AI decisions
   
   Please use the CLI or direct API calls for unsupported actions."
   ```

2. **Log the missing feature**:
   ```bash
   tasker reasoning log --issue <current-issue> \
     --thought "User requested unsupported action: <action>" \
     --decision "Notify user" \
     --alternatives "Implement new endpoint, Use direct API"
   ```

---

## Mandatory Tasker Operations

All of these MUST be done through Tasker:

### Issue Management
- Create issues → `POST /api/v1/issues`
- List issues → `GET /api/v1/issues`
- Update issues → `PATCH /api/v1/issues/{id}`
- Close issues → `POST /api/v1/issues/{id}/close`
- Add dependencies → `POST /api/v1/dependencies`
- Check blocked issues → `GET /api/v1/issues/blocked`

### Component Management
- Create components → `POST /api/v1/components`
- List components → `GET /api/v1/components`
- Get component details → `GET /api/v1/components/{id}`
- Update component → `PATCH /api/v1/components/{id}`

### Documentation
- Sync documentation → `tasker docs sync`
- Update changelog → Log in `VERSIONS.md` via tasker
- Track spec changes → Create issues for spec modifications

### Code Analysis
- Scan code graph → `tasker code-graph scan .`
- Impact analysis → `POST /api/v1/code-graph/impact`
- Find symbols → `GET /api/v1/code-graph/symbols`

### Agent Management
- Register agent → `POST /api/v1/agents/register`
- Specialize agent → `POST /api/v1/agents/{id}/specialists/{component_id}`
- Log reasoning → `POST /api/v1/reasoning/log`

---

## Example Scenarios

### Scenario 1: User asks about project status
```
User: "¿Cuál es el estado actual del proyecto?"
Agent: *detects "proyecto" keyword*
  → GET /projects/current
  → Returns project details with status
  → Displays summary to user
```

### Scenario 2: User asks to create an issue
```
User: "Create an issue for the login bug"
Agent: *detects "issue" keyword*
  → POST /api/v1/issues
  → Returns created issue with ID
  → Confirms to user with issue details
```

### Scenario 3: User asks about code structure
```
User: "What are the main components of the codebase?"
Agent: *detects "componentes" keyword*
  → GET /api/v1/components
  → Returns component list from Tasker
  → Presents organized component hierarchy
```

### Scenario 4: User requests documentation update
```
User: "Update the README with the new API endpoints"
Agent: *detects "documentación" keyword*
  → Check existing docs in Tasker
  → Create issue for docs update: `POST /api/v1/issues`
  → After changes, update docs via tasker
```

### Scenario 5: User requests unsupported action
```
User: "Generate a Gantt chart for the project timeline"
Agent: *detects project-related keyword*
  → Checks available Tasker endpoints
  → "This feature is not yet available in Tasker.
     Tasker currently supports issue-based tracking,
     not timeline/Gantt visualization.
     
     Available alternatives:
     1. Use tasker issue list to see work items
     2. Export issues to external tool for visualization"
```

---

## Important Notes

1. **Never bypass Tasker**: All project management must go through Tasker API/CLI.
2. **Always return Tasker data**: When querying project info, show the data from Tasker, not assumptions.
3. **Update Tasker first**: Before creating files or making changes, create/update issues in Tasker.
4. **Log all reasoning**: Use `tasker reasoning log` to track why decisions were made.
5. **Documentation via Tasker**: All doc updates must be tracked as issues or via tasker commands.

---

## CLI Reference for Agents

```bash
# Project info
tasker project show
tasker project list

# Issues
tasker issue list
tasker issue show <id>
tasker issue create --title "..." --priority HIGH
tasker issue update <id> --status IN_PROGRESS
tasker issue close <id>

# Components
tasker component list
tasker component show <id>
tasker component create --name "..." --description "..."

# Agents
tasker agent status
tasker agent register --id <id> --name <name> --role <role>
tasker agent specialize --agent <id> --component <comp>

# Documentation
tasker docs sync
tasker docs generate

# Code Analysis
tasker code-graph scan .
tasker code-graph impact <symbol>

# Reasoning
tasker reasoning log --issue <id> --thought "..." --decision "..."

# RAG
tasker rag search "<query>"
```

---

## See Also

- [AGENT_GUIDE.md](./AGENT_GUIDE.md) - Full agent protocol
- [API_REFERENCE.md](../../docs/API_REFERENCE.md) - Complete API documentation
- [ONBOARDING.md](../../docs/ONBOARDING.md) - Setup and configuration