# Issue #47: Fix component delete by name not working

## Description

When trying to delete a component by name (not ID), the command fails with "Component 'Name' not found."

### Command Executed
```bash
tasker --file-path "./data" component delete ToDelete --force
```

### Expected Behavior
Should find component by name and delete it.

### Actual Behavior
```
Component 'ToDelete' not found.
```

### Steps to Reproduce
1. Create component: `tasker component create ToDelete -p test`
2. Try to delete: `tasker component delete ToDelete --force`
3. Error: "Component 'ToDelete' not found."

### Solution

The `component delete` command should accept either a name or an ID. Need to check if the input is a valid UUID (ID) or a name, and search accordingly.

**Resolution**: Modified `component_delete` in `commands.py` to:
1. Try to parse input as UUID first
2. If not a valid UUID, search components by name (case-insensitive)
3. If found, use the resolved ID for deletion

## Status: COMPLETED