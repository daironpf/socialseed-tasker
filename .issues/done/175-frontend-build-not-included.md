# Issue #175 - Frontend Build Not Included in Scaffold

## Description

When running `tasker init`, the scaffolded frontend is just a basic placeholder HTML, NOT the full Vue Kanban board application.

## Expected Behavior

`tasker init` should deploy the full frontend Vue application (from `frontend/dist/`) so users get a working board immediately.

## Actual Behavior

- Template files: `assets/templates/frontend/` contains only basic files (~2KB total)
- Real frontend: `frontend/dist/` contains full Vue app (865KB)
- User gets placeholder HTML, not the Kanban board

## Steps to Reproduce

1. Run `tasker init .` in a new directory
2. Check `tasker/frontend/` - it's just basic HTML, not the full Vue app
3. User must manually copy `frontend/dist/` to get a working board

## Root Cause

The scaffolder in `src/socialseed_tasker/core/system_init/scaffolder.py` copies templates from `assets/templates/frontend/`, but those are placeholder files, not the actual build from `frontend/dist/`.

## Affected File

`src/socialseed_tasker/core/system_init/scaffolder.py`

## Suggested Fix

Option 1: Copy frontend/dist/ during scaffold if it exists:
```python
# In scaffolder.py, after copying templates, add:
frontend_dist = target_dir.parent / "frontend" / "dist"
if frontend_dist.exists():
    # Copy to tasker/frontend/
```

Option 2: Include frontend/dist/ in package assets (will increase package size)

Option 3: Use a build step in Dockerfile to build from source during docker-compose up

## Status: COMPLETED