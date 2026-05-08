# AI Agent Guide: Interacting with Tasker

This guide defines the protocol for AI agents working on this project. To ensure project health and visibility, agents MUST follow these rules.

## 1. Context First
Before starting any task, read `.agent/project.md` to understand the architecture, constraints, and quality standards.

## 2. Agent Registration (Required)
Before performing any task, agents MUST register themselves with Tasker. This enables tracking, specialization, and project assignment.

### Register Agent
```bash
curl -X POST "http://localhost:8000/api/v1/agents/register" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-001",
    "name": "Developer Agent",
    "role": "developer",
    "capabilities": ["coding", "testing", "code-review"]
  }'
```

**Parameters:**
| Field | Type | Description |
|-------|------|-------------|
| `agent_id` | string | Unique identifier (e.g., "agent-001", "reviewer-bot") |
| `name` | string | Human-readable name |
| `role` | string | Role: `developer`, `reviewer`, `planner`, `observer` |
| `capabilities` | array | List of capabilities (e.g., ["coding", "testing"]) |

### Agent Specialization
Agents can specialize in specific components for domain-driven dispatching:
```bash
# Add specialization
curl -X POST "http://localhost:8000/api/v1/agents/{agent_id}/specialists/{component_id}"

# List agent's specializations
curl "http://localhost:8000/api/v1/agents/{agent_id}/specialists"

# List component's specialists
curl "http://localhost:8000/api/v1/components/{component_id}/specialists"
```

## 3. Issue-Driven Development
All work must be tied to an issue in Tasker.
- **Find Work**: Use `tasker issue list` or check the Kanban board at `http://localhost:8080`.
- **Start Work**: Mark the issue as "IN PROGRESS" or log a reasoning entry stating you are starting.

## 4. Log Your Reasoning
Tasker isn't just for tracking tasks; it's for tracking **why** decisions were made.
- **Log Decisions**: When you make an architectural choice or resolve a complex bug, use:
  ```bash
  tasker reasoning log --issue <ID> --thought "I am choosing X because Y" --decision "Use X"
  ```
- **Why?**: This builds the "Organizational Memory" that future agents and humans will use to understand the codebase.

## 5. Query the Knowledge Base (RAG)
Before solving a problem, check if it has been solved before or if there are Architectural Decisions (ADRs) that guide the solution:
```bash
tasker rag search "how to implement caching"
```
This will return relevant context from past issues, ADRs, and documentation to guide your implementation.

## 6. Keep the Code Graph Updated
If you add or modify files, update the project's knowledge graph to enable impact analysis:
```bash
tasker code-graph scan . --incremental
```

## 7. Documentation Sync
When an issue is completed, update the project documentation in the root directory:
- **ROADMAP.md**: Mark the task as resolved in the Known Issues table.
- **VERSIONS.md**: Add the feature/bugfix to the current version checklist.
- **README.md**: Update if new commands or public features were added.

## 8. Closing the Loop
When finished:
1. Run project tests.
2. Log final results/thoughts.
3. Close the issue: `tasker issue close <ID>`.
   *(Note: Closing the issue automatically generates semantic RAG embeddings of your solution for future agents!)*

## Summary of Commands
| Action | Command |
|---|---|
| Register agent | `tasker agent register --id <id> --name <name> --role <role>` |
| List issues | `tasker issue list` |
| Impact analysis | `tasker code-graph impact <Symbol>` |
| Search knowledge | `tasker rag search "<query>"` |
| Log reasoning | `tasker reasoning log --issue <ID> ...` |
| Update graph | `tasker code-graph scan .` |
| Close issue | `tasker issue close <ID>` |
| Agent specialist | `tasker agent specialize --agent <id> --component <comp>` |

## See Also

- [Full Documentation](../../docs/ONBOARDING.md) - Complete onboarding guide
- [API Reference](../../docs/API_REFERENCE.md) - Full API endpoints
- [Implementation Guide](../../docs/IMPLEMENTATION_GUIDE.md) - Extending the graph
- [Troubleshooting Guide](../../docs/TROUBLESHOOTING.md) - Common issues and solutions
