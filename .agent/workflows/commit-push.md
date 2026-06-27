# Workflow: Prepare for Commit (User Approval Required)

## IMPORTANT: Agent Must NOT Commit

**The agent MUST NOT execute `git commit` or `git push`.** This action requires explicit user approval.

The agent's role is to:
1. Prepare the changes
2. Present a summary for the user to review
3. Wait for user to approve and execute the commit

---

## When to Use

After implementing an issue and all tests pass. The agent should NOT commit directly.

---

## Steps for Agent

### 1. Check Status

```bash
git status
```

Review what files have changed.

### 2. Review Changes

```bash
git diff
```

Verify the changes are correct and complete.

### 3. Check Recent Commits

```bash
git log --oneline -5
```

Note the existing commit message style.

### 4. Check Documentation Updates

**IMPORTANT:** Before proposing a commit, check if documentation needs updating. See `skills/documentation-sync.md` for guidance.

Common documentation files to check:
- `README.md` - New commands, API endpoints, env vars
- `ROADMAP.md` - Resolved known issues
- `VERSIONS.md` - Current version checklist

### 5. Present Commit Summary to User

Generate a summary with:

**Changed files:**
```
<list of files>
```

**Proposed commit message:**
```
type: short summary

- Detailed change 1
- Detailed change 2
- All tests pass
```

---

## Commit Message Types

| Type | When to Use | Example |
|------|-------------|---------|
| `feat` | New feature or capability | `feat: implement Issue and Component entities` |
| `fix` | Bug fix | `fix: correct Neo4j port configuration` |
| `test` | Adding or fixing tests | `test: add entity validation tests` |
| `docs` | Documentation changes | `docs: update README with setup instructions` |
| `chore` | Maintenance tasks | `chore: update dependencies` |
| `refactor` | Code restructuring without behavior change | `refactor: extract repository protocol` |

---

## User Action Required

The agent MUST present the commit summary and **wait for the user to**:

1. Review the changes
2. Approve or modify the commit message
3. Execute `git commit` and `git push` themselves

### Example Agent Response

```
✅ All changes ready for review

**Changed files:**
- src/core/task_management/entities/issue.py
- tests/unit/test_issue.py

**Proposed commit message:**
```
fix: add issue validation

- Added required field validation for Issue entity
- Added unit tests for validation logic
- All tests pass
```

📋 **To complete this commit, please run:**
```bash
git add src/ tests/
git commit -m "fix: add issue validation"
git push
```
```

---

## Rules

- **NEVER** execute `git commit` as the agent
- **NEVER** execute `git push` as the agent
- Always present a summary for user review
- Check documentation updates before proposing commit
- All commit messages must be in English

---

## Anti-Patterns

- Agent executing git commit without user approval
- Agent force pushing
- Skipping tests before proposing commit
- Using generic commit messages without detailed summary