# AI Agent Guide: Interacting with Tasker

This guide defines the protocol for AI agents working on this project. To ensure project health and visibility, agents MUST follow these rules.

## 1. Context First
Before starting any task, read `.agent/project.md` to understand the architecture, constraints, and quality standards.

## 2. Issue-Driven Development
All work must be tied to an issue in Tasker.
- **Find Work**: Use `tasker issue list` or check the Kanban board at `http://localhost:8080`.
- **Start Work**: Mark the issue as "IN PROGRESS" or log a reasoning entry stating you are starting.

## 3. Log Your Reasoning
Tasker isn't just for tracking tasks; it's for tracking **why** decisions were made.
- **Log Decisions**: When you make an architectural choice or resolve a complex bug, use:
  ```bash
  tasker reasoning log --issue <ID> --thought "I am choosing X because Y" --decision "Use X"
  ```
- **Why?**: This builds the "Organizational Memory" that future agents and humans will use to understand the codebase.

## 4. Query the Knowledge Base (RAG)
Before solving a problem, check if it has been solved before or if there are Architectural Decisions (ADRs) that guide the solution:
```bash
tasker rag search "how to implement caching"
```
This will return relevant context from past issues, ADRs, and documentation to guide your implementation.

## 5. Keep the Code Graph Updated
If you add or modify files, update the project's knowledge graph to enable impact analysis:
```bash
tasker code-graph scan . --incremental
```

## 6. Documentation Sync
When an issue is completed, update the project documentation in the root directory:
- **ROADMAP.md**: Mark the task as resolved in the Known Issues table.
- **VERSIONS.md**: Add the feature/bugfix to the current version checklist.
- **README.md**: Update if new commands or public features were added.

## 7. Closing the Loop
When finished:
1. Run project tests.
2. Log final results/thoughts.
3. Close the issue: `tasker issue close <ID>`.
   *(Note: Closing the issue automatically generates semantic RAG embeddings of your solution for future agents!)*

## Summary of Commands
| Action | Command |
|---|---|
| List issues | `tasker issue list` |
| Impact analysis | `tasker code-graph impact <Symbol>` |
| Search knowledge | `tasker rag search "<query>"` |
| Log reasoning | `tasker reasoning log --issue <ID> ...` |
| Update graph | `tasker code-graph scan .` |
| Close issue | `tasker issue close <ID>` |
