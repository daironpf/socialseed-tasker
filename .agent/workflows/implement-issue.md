# Workflow: Implement an Issue

## When to Use

When instructed to implement a specific issue from `.issues/`.

## Steps

### 1. Read the Issue

```
Read .issues/{NN}-{issue-name}.md
```

Understand all requirements before writing any code.

### 2. Plan the Implementation

Identify:
- Which files need to be created or modified
- What tests are needed
- What dependencies are required

### 3. Implement the Code

- Follow hexagonal architecture conventions (see `skills/hexagonal-architecture.md`)
- No business logic in entrypoints or storage layers
- Pure Python in `core/` - no external framework imports
- All code in English

### 4. Write Tests

- Create tests in `tests/unit/` for core logic
- Create tests in `tests/integration/` for storage/entrypoint integration
- See `workflows/test-code.md` for testing procedures

### 5. Run Tests

```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```

All tests must pass before proceeding.

### 6. Mark Issue as Completed

Edit the issue file:
```markdown
## Status: PENDING
```
Change to:
```markdown
## Status: COMPLETED
```

### 7. Move Issue to Done

```bash
mv ".issues/{NN}-{issue-name}.md" ".issues/done/"
```

### 8. Update Documentation (if needed)

See `skills/documentation-sync.md` for full procedure. Quick check:

- Does this fix a known issue? → Update `ROADMAP.md` known issues table
- Does this add a feature? → Update `VERSIONS.md` checklist
- Does this add a new command? → Update `README.md`
- Does this change APIs? → Update `API_REFERENCE.md`

**Always run** `skills/documentation-sync.md` guidance to determine what docs need updating.

### 9. Commit and Push

Create a detailed commit following the conventional commits format with a comprehensive summary:

```bash
git add src/ tests/ README.md ROADMAP.md VERSIONS.md
git commit -m "type: short summary

- Detailed description of changes made
- Specific files modified and why
- Test results and verification
- Issue reference and completion status
- Documentation updates if applicable"
git push origin v0.8.0
```

**Commit Message Structure:**
```
type: short summary

- Change 1: specific description
- Change 2: specific description
- Change 3: specific description

All tests pass. Issue moved to .issues/done/.
```

**Types:**
| Type | When to Use |
|------|-------------|
| `fix` | Bug fixes |
| `feat` | New features |
| `refactor` | Code restructuring |
| `test` | Adding/updating tests |
| `docs` | Documentation changes |
| `chore` | Maintenance tasks |

## Checklist

- [ ] Issue fully read and understood
- [ ] Code follows hexagonal architecture
- [ ] Tests written and passing
- [ ] Issue marked as COMPLETED
- [ ] Issue moved to `.issues/done/`
- [ ] Documentation updated (if applicable)
- [ ] Committed with conventional commit message
- [ ] Pushed to remote
