# Skill: Issue-Driven Development

## Description

This project uses an issue-driven development workflow. All work is tracked via markdown files in `.issues/`. Agents must read, implement, and manage issues following strict conventions.

## Issue File Structure

Issues live in `.issues/` with the naming convention:

```
{NN}-{kebab-case-title}.md
```

Example: `03-define-task-repository-interface-and-actions.md`

### Issue File Format

```markdown
# Issue #{NN}: Title

## Description

Detailed technical requirements and specifications.

## Status: PENDING | COMPLETED
```

## Workflow

1. **Read** the issue file in `.issues/` to understand requirements
2. **Implement** the code following the specifications
3. **Test** the implementation (see `workflows/test-code.md`)
4. **Mark as completed** by changing `## Status: PENDING` to `## Status: COMPLETED`
5. **Move** the file to `.issues/done/`
6. **Commit and push** (see `workflows/commit-push.md`)

## Rules

- NEVER skip an issue - work sequentially unless instructed otherwise
- NEVER modify `.issues/done/` files after moving them there
- ALWAYS read the full issue before writing any code
- If requirements are ambiguous, ask the user before proceeding
