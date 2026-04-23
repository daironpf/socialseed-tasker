# Skill: Documentation Synchronization

## Description

This skill ensures documentation stays synchronized with code changes. Every time an issue is resolved, check if documentation updates are needed.

## When to Use

Whenever completing an issue from `.issues/to-do/` - specifically when the fix involves:
- New features or commands
- Bug fixes that affect user-visible behavior
- API changes
- Configuration changes
- Test coverage improvements

## Documentation Files to Check

| File | When to Update |
|------|----------------|
| `README.md` | New CLI commands, API endpoints, environment variables |
| `ROADMAP.md` | Resolved known issues, new features completed |
| `VERSIONS.md` | All issue numbers in the current version checklist |
| `CHANGELOG.md` | User-facing changes, bug fixes, new features |
| `API_REFERENCE.md` | Any REST API changes |
| `.agent/skills/*.md` | Environment or tooling changes |

## Sync Workflow

### Step 1: Identify Documentation Impact

After fixing an issue, ask:
- Does this add a new CLI command? → Update README.md, skills
- Does this fix a known issue? → Update ROADMAP.md known issues table
- Does this add a feature to current version? → Update VERSIONS.md checklist
- Does this affect users? → Consider CHANGELOG.md

### Step 2: Make the Updates

#### ROADMAP.md Updates

1. Update "Last updated" date at top
2. Add feature to appropriate phase if new
3. Mark resolved issue in Known Issues table:
   ```
   | # | Description | Severity | Location | ✅ RESOLVED (v0.8.0 #XXX) |
   ```

#### VERSIONS.md Updates

1. Add issue number to current version checklist:
   ```
   - [x] **#XXX Description:** What was fixed or added.
   ```
2. If starting new version, add to Version Reference table

#### README.md Updates

1. Update version badge if needed
2. Add new command examples in Quick Start
3. Add new API endpoints in REST API section
4. Update environment variables table if needed

### Step 3: Commit with Docs

Include documentation in the same commit as the fix:

```bash
git add src/ tests/ README.md ROADMAP.md VERSIONS.md
git commit -m "fix(feature): description

- Updated README with new command
- Updated ROADMAP with resolved issue
- Updated VERSIONS checklist

Issue #XXX resolved."
```

## Example: Resolving a CLI Enhancement Issue

### Issue #136: Add name lookup to component update

**Code changes:** `commands.py` - add `resolve_component_id()` call

**Documentation changes needed:**
1. **ROADMAP.md**: 
   - Update "Last updated" to current date
   - Add to Known Issues: `| 10 | component update requires full UUID | Low | CLI | ✅ RESOLVED (v0.8.0 #136) |`

2. **VERSIONS.md**:
   - Add to v0.8.0 bug fixes: `- [x] **#136 CLI Component Update Name:** Support name lookup in component update command.`

3. **README.md**:
   - Update command example to show name works: `tasker component update backend -n "New Name"`

## Anti-Patterns to Avoid

- **Don't update docs in a separate commit** - keeps context together
- **Don't skip docs because "it's obvious"** - future maintainers need context
- **Don't over-document** - only update what's directly affected
- **Don't forget the version** - always include issue number

## Important Notes

- The `.issues/to-do/` and `.issues/done/` directories are **gitignored** - they are local tracking only
- Documentation changes ARE committed to git - they are part of the project
- Always include issue number in commit message and docs
- Run tests before committing to ensure nothing broke

## Quick Reference

```bash
# After fixing an issue:
1. Identify which docs need updates
2. Edit ROADMAP.md, VERSIONS.md, README.md as needed
3. Run tests: .venv/Scripts/python.exe -m pytest tests/ -v
4. Commit everything together
5. Push to remote
```

## Related Skills

- [issue-driven-development](./issue-driven-development.md) - Issue workflow
- [environment-tooling](./environment-tooling.md) - Project structure
- [project-testing](./project-testing.md) - Testing conventions