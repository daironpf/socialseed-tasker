# Workflow: Commit and Push

## When to Use

After implementing an issue and all tests pass.

## Steps

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

Follow the existing commit message style.

### 4. Stage and Commit

**IMPORTANT:** Before committing, check if documentation needs updating. See `skills/documentation-sync.md` for guidance.

Common documentation files to check:
- `README.md` - New commands, API endpoints, env vars
- `ROADMAP.md` - Resolved known issues
- `VERSIONS.md` - Current version checklist
- `CHANGELOG.md` - User-facing changes

```bash
# Include docs if they were updated
git add src/ tests/ README.md ROADMAP.md VERSIONS.md
git commit -m "type: detailed summary"
```

### Commit Message Structure

Use the format: `type: short summary` followed by a blank line and a detailed summary of changes.

**Example:**
```
feat: add AI reasoning logs to issues

- Added ReasoningLogEntry value object with ReasoningContext enum
- Added reasoning_logs field to Issue entity
- Added API schemas and endpoints for reasoning logs
- Added repository methods for Neo4j storage
- Added unit tests for new functionality

All tests pass. Issue moved to .issues/done/.
```

### Commit Message Types

| Type | When to Use | Example |
|------|-------------|---------|
| `feat` | New feature or capability | `feat: implement Issue and Component entities` |
| `fix` | Bug fix | `fix: correct Neo4j port configuration` |
| `test` | Adding or fixing tests | `test: add entity validation tests` |
| `docs` | Documentation changes | `docs: update README with setup instructions` |
| `chore` | Maintenance tasks | `chore: update dependencies` |
| `refactor` | Code restructuring without behavior change | `refactor: extract repository protocol` |

### 5. Push to Remote

```bash
git push origin v0.8.0
```

## Rules

- ALWAYS check `skills/documentation-sync.md` for docs updates before committing
- NEVER commit secrets, keys, or credentials
- NEVER commit `.env` files
- NEVER commit generated data (neo4j/data, logs, etc.)
- NEVER skip tests before committing
- Only commit when explicitly asked or after completing an issue
- One commit per issue implementation
- Commit message should include a detailed summary of what was changed (the same summary provided when completing the issue)
- All commit messages must be in English

## Anti-Patterns

- Amending commits that have already been pushed
- Force pushing to main
- Committing without running tests first
- Including `.issues/` files in commits (they are gitignored)
- Using short generic commit messages without detailed summary
