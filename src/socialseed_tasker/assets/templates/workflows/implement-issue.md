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

### 3. Implement the Code
- Follow the architectural patterns defined in `tasker/project.md`.
- All code and comments must be in English.

### 4. Write and Run Tests
- Create unit/integration tests as needed.
- Ensure all tests pass.

### 5. Mark Issue as Completed
```bash
tasker issue close <ID> --reason "Implementation complete and verified by tests"
```

### 6. Update Documentation
- Follow `tasker/AGENT_GUIDE.md` for doc-sync procedures.
- Update `ROADMAP.md` and `VERSIONS.md`.

### 7. Commit Changes
Use conventional commits:
```bash
git add .
git commit -m "feat: implement <issue description>"
```

## Checklist
- [ ] Issue requirements fully understood.
- [ ] Impact analysis performed.
- [ ] Code follows project standards.
- [ ] Tests written and passing.
- [ ] Documentation updated.
- [ ] Issue closed in Tasker.
