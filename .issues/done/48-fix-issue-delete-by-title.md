# Issue #48: Fix issue delete by title not working

## Description

When trying to delete an issue by title (not ID), the command fails with "Issue 'Title' not found."

### Command Executed
```bash
tasker --file-path "./data" issue delete IssueToDelete --force
```

### Expected Behavior
Should find issue by title and delete it.

### Actual Behavior
```
Issue 'IssueToDelete' not found.
```

### Steps to Reproduce
1. Create issue: `tasker issue create IssueToDelete -c <component-id> -p LOW`
2. Try to delete: `tasker issue delete IssueToDelete --force`
3. Error: "Issue 'IssueToDelete' not found."

### Solution

The `issue delete` command should accept either a title/partial ID or a full ID. Need to implement lookup by title in addition to ID.

**Resolution**: Modified `issue_delete` in `commands.py` to:
1. Try to parse input as UUID first
2. If not a valid UUID, search issues by exact title or partial match (case-insensitive)
3. If found, use the resolved ID for deletion

## Status: COMPLETED