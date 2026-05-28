# Project Versions

## [1.0.2] - 2026-05-28

### v1.0.2 Checklist
- [x] **#330 Docker build context:** Fixed `docker-compose.yml` template — changed build context to `../..` with `dockerfile: .agent/tasker/Dockerfile` so `COPY pyproject.toml README.md ./` resolves from project root.
- [x] **#331 Policy NameError:** Added missing `as queries` import alias in `neo4j_policy_repository.py`, `neo4j_user_repository.py`, `neo4j_commit_repository.py`, and `neo4j_code_graph_repository.py` — all used `queries.XXX` but imported as `neo4j_queries`.
- [x] **#332 DB disconnect error:** Added detection of `neo4j.exceptions.ServiceUnavailable`/`Neo4jError`/`SessionExpired` in the generic FastAPI exception handler — now returns `503 DATABASE_CONNECTION_ERROR` with the actual error message instead of a generic `500 INTERNAL_ERROR`.
- [x] **#333 Windows emoji crash:** Replaced `🎉` (party popper) with plain `SUCCESS:` text in `init_command.py` to avoid `UnicodeEncodeError` on Windows cp1252 terminals.
- [x] **#342 Terminal emoji crash:** Replaced emojis in `issue_commands.py` and changed `raise typer.Exit` to `sys.exit` in `app.py`.
- [x] **#343 API error traceback:** Changed `logger.error` to `logger.debug` in `api_client.py`.
- [x] **#344 CLI --depends-on mismatch:** Added `--depends-on`/`-d` option to `dependency add/remove` while keeping positional args for backward compatibility.
- [x] **#345 Non-TTY piped input crash:** Wrapped `Prompt.ask()`/`typer.confirm()` with EOFError fallback to `input()` in `init_command.py`.

## [1.0.1] - 2026-05-25

### v1.0.1 Checklist
- [x] **#326 Schema init CypherSyntaxError:** Fixed invalid `DEPENDS_ON` relationship index syntax in `neo4j_queries.py` — changed `(i:Issue) ON (i.timestamp)` to `() ON (r.timestamp)`.
- [x] **#327 NameError on logger:** Added missing `logger = logging.getLogger(__name__)` in `neo4j_driver.py` to prevent crash in exception handlers.
- [x] **#328 Docker build 403 Forbidden:** Removed `COPY --from=ghcr.io/lexifuse/neo4j-mcp-server` from Dockerfiles — ghcr.io requires auth for anonymous pulls, causing build failure.
- [x] **#329 Frontend doc gap:** Added "Frontend (Vue.js Kanban Board)" section to scaffold README template documenting the placeholder frontend, build steps, and customization guide.

## [1.0.0] - 2026-05-22

### v1.0.0 Checklist
- [x] **#001-#325 All Issues:** All 325+ issues are resolved across scaffolding, API, CLI, frontend, Neo4j, Docker, agents, code-graph, RAG, secrets, contracts, CI/CD, and release automation.

### Release History
| Version | Date | Description |
|---------|------|-------------|
| 1.0.2   | 2026-05-28 | Bugfix: Docker build context, policy NameError, DB error handler, Windows emoji, CLI --depends-on flag, non-TTY init |
| 1.0.1   | 2026-05-25 | Bugfix: Schema init CypherSyntaxError & logger NameError |
| 1.0.0   | 2026-05-24 | Full Release — All issues resolved |
