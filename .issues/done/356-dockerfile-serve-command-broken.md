# Issue #356: Dockerfile scaffold uses `tasker serve` which doesn't exist in installed package

## Description
The scaffolded `.agent/tasker/Dockerfile` uses `CMD ["tasker", "serve", ...]` but in the installed package (from PyPI or editable install), the `serve` command is not recognized. The API container repeatedly crashes with: "No such command 'serve'. Did you mean 'seed'?"

## Expected Behavior
The Docker container should start the API server successfully.

## Actual Behavior
Container crashes immediately with "No such command 'serve'".

## Steps to Reproduce
1. Run `tasker install .`
2. Run `docker compose build tasker-api`
3. Run `docker compose up tasker-api`
4. Check logs — "No such command 'serve'" error

## Status: PENDING

## Priority: HIGH

## Component
Docker

## Suggested Fix
Change CMD to: `CMD ["python", "-m", "socialseed_tasker.infrastructure.web_api.__main__"]`

## Impact
New users cannot start the API server using the scaffolded Docker setup.
