# Workflow: Implement an Issue

## When to Use
When instructed to implement a specific issue from Tasker.

## Steps

### 1. Read the Issue
```bash
tasker issue show <ID>
```
Understand all requirements and acceptance criteria before writing any code.

### 2. Plan the Implementation
Identify:
- Which files need to be created or modified.
- What tests are needed.
- Impact on existing systems (use `tasker code-graph impact <Symbol>`).

### 3. Log Reasoning (v1.0 Traceability)
Before writing code, log your plan and the alternatives you considered:
```bash
tasker reasoning log --issue <ID> \
  --thought "Plan: Implement X using Y. Alternatives: Z." \
  --alternatives "Z, W" \
  --rejected "Z is too slow, W is complex" \
  --decision "Implementing X"
```

### 4. Implement the Code
- Follow the architectural patterns defined in `tasker/project.md`.
- All code and comments must be in English.

### 5. Update Code Graph
After modifying the code, you MUST update the knowledge graph:
```bash
tasker code-graph scan . --incremental
```

### 6. Write and Run Tests
- Create unit/integration tests as needed.
- Ensure all tests pass.

### 7. Mark Issue as Completed
Close the issue and link it to the modified files:
```bash
tasker issue close <ID> --files "path/to/file1.py,path/to/file2.py"
```

### 8. Update Documentation
- Follow `tasker/AGENT_GUIDE.md` for doc-sync procedures.
- Update `ROADMAP.md` and `VERSIONS.md`.

### 7. Prepare for Commit (User Approval Required)
**DO NOT commit as the agent.** Present a summary for user to review and approve.

Generate a summary with:
- List of modified files
- Proposed commit message following conventional commits

Wait for user to execute `git commit` and `git push`.

See `workflows/commit-push.md` for details.

## Checklist
- [ ] Issue requirements fully understood.
- [ ] Impact analysis performed.
- [ ] Code follows project standards.
- [ ] Tests written and passing.
- [ ] Documentation updated.
- [ ] Issue closed in Tasker.
