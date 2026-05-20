# Agent Skills & Workflows

This directory contains the operational knowledge for AI agents working on this project.

## Directory Structure
```
.agent/
├── skills/          # Specialized capabilities (API interaction, impact analysis)
└── workflows/       # Step-by-step procedural guides
```

## Quick Reference
| Task | Workflow | Description |
|---|---|---|
| `SETUP` | `workflows/project-setup.md` | Initialize or re-scaffold project modules |
| `INIT` | `workflows/interactive-init.md` | **Interactive** - Guide user through `tasker init` with recommendations |
| `ISSUE` | `workflows/create-issue.md` | Create new tasks based on analysis or user request |
| `WORK` | `workflows/implement-issue.md` | Start working on a specific issue |
| `DOCS` | `workflows/update-documentation.md` | Sync all documentation (Code, MD, Web) |
| `HISTORY`| `workflows/daily-log.md` | Update the daily log (bitácora) in `.history/` |
| `TEST` | `workflows/prueba-el-proyecto.md` | Full black-box evaluation of the project |
| `COMMIT`| `workflows/commit-push.md` | Prepare changes for user approval |
| `FIND` | `workflows/convert-findings-to-issues.md` | Convert test report findings into actionable issues |
| `PROJECT` | `workflows/project-centric-agent.md` | **CRITICAL** - Always consult Tasker for project-related info |

## Agent Protocol
For detailed rules on how to interact with Tasker and the project, read **[AGENT_GUIDE.md](./AGENT_GUIDE.md)**.

### Single Project Rule
**Tasker supports only ONE project per instance.** All issues, components, agents, and code symbols belong to this single project. When registering an agent, it is automatically assigned to the existing project.

### Service Menu Rule
- **Always end with a Service Menu**: At the end of every response where a task was completed or a decision is needed, present a table of available workflows.
- **Suggest Next Steps**: Based on the current state, highlight the most logical next workflow in **bold**.
- **Wait for Choice**: Unless it's an emergency, wait for the user to select an option (e.g., "1", "Create Issue") before proceeding.

## Core Files
- **project.md**: Project architecture, constraints, and quality standards.
- **project.json**: Machine-readable project metadata.