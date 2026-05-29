# Issue #347: Docker API Server Fails to Start - SyntaxError in commands.py f-string

## Description
The Docker API container fails to start with `SyntaxError: f-string: expecting '}'` at `commands.py:1278`. Nested quotes in f-string are incompatible with Python 3.10.

## Expected Behavior
The Docker API container should start successfully and serve the REST API on port 8888.

## Actual Behavior
Container exits immediately with Python SyntaxError:
```
File "/usr/local/lib/python3.10/site-packages/.../commands.py", line 1278
f"[bold]Risk level:[/bold] {"CRITICAL" if len(callers) > 5 else "HIGH" ...
                                ^^^^^^^^
SyntaxError: f-string: expecting '}'
```

## Steps to Reproduce
1. Run `docker compose --profile api up -d` from `.agent/tasker/`
2. Check container logs: `docker compose logs tasker-api`
3. Observe SyntaxError traceback

## Status: PENDING

## Priority: CRITICAL

## Component
DOCKER / CORE

## Suggested Fix
Use single quotes or extract the conditional to a variable to avoid nested quotation marks in f-strings. Example:
```python
risk = "CRITICAL" if len(callers) > 5 else "HIGH" if len(callers) > 2 else "MEDIUM" if len(callers) > 0 else "LOW"
f"[bold]Risk level:[/bold] {risk}"
```

## Impact
API server cannot run via Docker. CLI direct mode works as fallback, but the REST API, Swagger docs, and frontend board are unavailable via Docker.
