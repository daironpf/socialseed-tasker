# Issue #178 - Scaffold Frontend Still Uses Placeholder Templates

## Description

Even with the fix in issue #175, `tasker init` only copies placeholder templates for frontend when run in an isolated directory. The actual Vue build exists at `frontend/dist/` in the project root but is not included in scaffold output.

## Expected Behavior

When running `tasker init` from the socialseed-tasker project directory, the `tasker/frontend/` directory should contain the full compiled Vue application from `frontend/dist/`.

## Actual Behavior

```bash
$ cd real-test && tasker init .
$ ls real-test/tasker/frontend/
Dockerfile  env.d.ts  index.html  nginx.conf

# Expected output should include:
# index.html (compiled)
# assets/ (Vue bundles)
# nginx.conf
```

The scaffolder copies only the template files (~2KB), not the actual compiled Vue app from `frontend/dist/` (~865KB).

## Steps to Reproduce

1. From the socialseed-tasker project root:
   ```bash
   mkdir -p test-init && cd test-init
   tasker init .
   ```
2. Check `test-init/tasker/frontend/` - it's just basic HTML, not the full Vue app
3. User gets placeholder HTML, not the working Kanban board

## Root Cause

The fix implemented in #175 ( `_copy_frontend_build` method) only copies `frontend/dist/` if it exists in the **target** directory. When running `tasker init` in a new directory, there's no `frontend/dist/` to copy.

The scaffolder needs to either:
1. Know the location of the source project's `frontend/dist/`
2. Have `frontend/dist/` bundled as package assets
3. Trigger a frontend build during scaffolding

## Affected Files

- `src/socialseed_tasker/core/system_init/scaffolder.py`
- `src/socialseed_tasker/entrypoints/cli/init_command.py`

## Suggested Fix

Option 1: Include frontend/dist in package assets:
- Add `frontend/dist/` to package data in `pyproject.toml`
- Copy from package data during scaffold

Option 2: Use relative path from project root:
- The scaffolder is called from the project root where `frontend/dist/` exists
- Modify the code to look at `source_project/frontend/dist/` instead of `target/frontend/dist/`

Option 3: Build frontend during scaffold:
- Run `npm install && npm run build` in `frontend/` during scaffolding
- Requires npm/node in the environment

## Impact

Users get placeholder HTML after scaffolding, not the working Kanban board. They must manually copy the build or build it themselves.

## Implementation

1. **Included frontend build in package assets**:
   - Created `src/socialseed_tasker/assets/frontend/` with contents of `frontend/dist/`
   - Updated `pyproject.toml` to include `assets/frontend/**/*` in package data

2. **Updated ScaffolderService**:
   - Added `frontend_dir` parameter to constructor
   - `_copy_frontend_build` now checks `self._frontend_dir` first (package assets)
   - Falls back to `target_dir/frontend/dist` if package assets not available

3. **Updated init_command.py**:
   - Added `_get_frontend_dir()` helper
   - Passes frontend directory to ScaffolderService

## Verification

```bash
$ mkdir test && cd test
$ tasker init .
# Now includes full Vue build:
# tasker/frontend/index.html (compiled)
# tasker/frontend/assets/*.js (Vue bundles ~865KB)
```

## Status: COMPLETED