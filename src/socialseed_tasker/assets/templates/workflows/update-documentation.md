# Workflow: Update Documentation (Doc-Sync)

## When to Use
Whenever a feature is added, a bug is fixed, or any user-visible change is made.

## Files to Update

| File | When to Update |
|------|----------------|
| `README.md` | New commands, environment variables, or quickstart changes. |
| `ROADMAP.md` | Mark issues as resolved in the "Known Issues" table. |
| `VERSIONS.md` | Add entry to the current version checklist/history. |
| `tasker/project.md` | Significant architectural changes or new core modules. |

## Steps

### 1. Identify Impact
Determine which documentation files are affected by your changes.

### 2. Apply Updates
- **ROADMAP.md**: Update the status to `✅ RESOLVED`.
- **VERSIONS.md**: Add the issue number and a brief description of the change.
- **README.md**: Add examples of new CLI commands or API endpoints.

### 3. Verify
Read through the updated files to ensure clarity and correctness.

### 4. Commit with Code
Always include documentation updates in the same commit as the code changes to keep history synchronized.
