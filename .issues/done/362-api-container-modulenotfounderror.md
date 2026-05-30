# Issue #362: API container crashes with ModuleNotFoundError

## Description
The scaffolded Dockerfile runs `pip install socialseed-tasker` from PyPI, but the published package does not include the `socialseed_tasker.infrastructure` module. The API container crashes on startup with `ModuleNotFoundError: No module named 'socialseed_tasker.infrastructure'`. The local development version has this module but it's not included in the PyPI release.

Users who install via `tasker init` in API mode will find the API container non-functional.

## Expected Behavior
The API container should start successfully when running `docker compose --profile api up -d`, serving the FastAPI REST API on port 8888.

## Actual Behavior
The container exits immediately with:
```
/usr/local/bin/python: Error while finding module specification for 'socialseed_tasker.infrastructure.web_api.__main__' (ModuleNotFoundError: No module named 'socialseed_tasker.infrastructure')
```

## Steps to Reproduce
1. Run `tasker install .` in a clean project
2. Run `tasker init` and select API mode
3. Wait for Docker compose to finish
4. Run `docker logs tasker-tasker-api-1`

## Status: PENDING

## Priority: CRITICAL

## Component
DOCKER

## Suggested Fix
Publish the full package to PyPI including all modules (`socialseed_tasker.infrastructure` and its subpackages), or change the Dockerfile to build from the local source code. Update the scaffold template to use `pip install -e .` or a multi-stage build that copies the source.

## Impact
API mode is completely broken for new users installing from PyPI. Only Direct (Neo4j Bolt) mode works. This blocks REST API usage, the Kanban frontend, and agent-based API integration.
