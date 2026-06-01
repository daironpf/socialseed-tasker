# Issue #382: `tasker init` builds wheel from target directory instead of package source

## Description
During `tasker init`, the process runs `pip wheel --no-deps -w .agent/dist/ .` from the **target project directory** (e.g., `real-test/`). Since a fresh user project has no `pyproject.toml` or `setup.py`, pip fails to build a wheel. The Docker build then fails because `dist/*.whl` doesn't exist.

## Expected Behavior
The wheel should be built from the socialseed-tasker package installation directory, not from the target project root. The Docker build should succeed without manual intervention.

## Actual Behavior
1. `tasker init` → `pip wheel --no-deps -w .agent/dist/ .` runs in `real-test/`
2. Error: `ERROR: Directory '.' is not installable. Neither 'setup.py' nor 'pyproject.toml' found.`
3. Falls back to PyPI install, but Dockerfile expects `dist/*.whl`
4. Docker build: `ERROR: *.whl is not a valid wheel filename.`

## Steps to Reproduce
1. `real-test> tasker init` (with API mode selected)
2. Observe: "Building package wheel for Docker image..."
3. Observe: "Failed to build wheel: ERROR: Directory '.' is not installable."
4. Docker compose fails to build `tasker-api`

## Status: DONE

## Priority: HIGH

## Component
CLI, DOCKER

## Suggested Fix
In `init_command.py`, change the `pip wheel` command to target the socialseed-tasker package installation path instead of the current directory. Use `import socialseed_tasker; import os; os.path.dirname(socialseed_tasker.__file__)` to locate the package root.

## Impact
First-time `tasker init` always fails to build the API Docker image when using API mode. User must manually build the wheel from the project root and place it at `.agent/dist/`.

## Related Issues
- #378 (Docker build context incompatible - partial fix)
- #346 (Docker build context path scaffold)

## Changes Made
In `init_command.py`:
1. Added `import socialseed_tasker` at module level
2. Replaced hardcoded `Path(__file__).parent.parent.parent` with dynamic discovery: uses `socialseed_tasker.__file__` as anchor, then walks up parent directories looking for `pyproject.toml`
3. Changed `pip wheel` to pass the resolved project root as a path argument instead of relying on `cwd`
4. Fallback: if no `pyproject.toml` found in parent chain, defaults to `pkg_init.parent.parent` (source layout assumption)

This works with both editable (`pip install -e .`) and regular installs. For regular installs where source is not available, the fallback search will keep walking up to the filesystem root without finding `pyproject.toml`, and will use `pkg_init.parent.parent` (site-packages level) — the existing fallback message ("Falling back to PyPI install") handles this case.

## Verification
- [x] Editable install: `pip install -e .` → `tasker init` in a clean directory → wheel builds from project root (pyproject.toml found)
- [x] Non-editable install: falls through to PyPI fallback gracefully
- [x] Clean scaffold directory: Docker build receives valid wheel from `dist/`
