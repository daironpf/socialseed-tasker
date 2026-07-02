# Project Versions

## [1.0.4] - 2026-07-02

### v1.0.4 Checklist
- [x] **FIND-001 Log noise:** Downgraded Neo4j connect/close INFO logs to DEBUG level so `[INFO] Neo4j connection closed` no longer appears in CLI output.
- [x] **FIND-002 doc-sync venv scan:** Added `IGNORE_DIRS` filter to doc-sync scanner to skip `venv/`, `.venv/`, `node_modules/`, and other common non-project directories.
- [x] **FIND-003 Config password loading:** `get_repository()` now falls back to reading `neo4j_password` from the `DualModeConfig` YAML config when the env var is not set.
- [x] **FIND-004 Exit code consistency:** Changed `typer.Exit(code=2)` to `code=1` for the "Neo4j password required" error.

## [1.0.3] - 2026-06-07

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
- [x] **#338 Rate-limit traceback:** Rate limiting returned raw Python traceback — fixed by structured error handler.
- [x] **#339 DB failure traceback:** DB connection failure printed traceback alongside structured error — fixed by error handler middleware.
- [x] **#340 Circular dependency UUID redundancy:** Error message repeated same UUID twice in dep path — deduplicated.
- [x] **#341 Exit code consistency:** Non-zero exit codes not consistently returned on failure — fixed by `sys.exit()` pattern.
- [x] **#346 Docker build context in blank project:** Updated `assets/templates/Dockerfile` to install from PyPI instead of copying local source, so it works without `pyproject.toml`/`src/`.
- [x] **Infra: Dockerfile base image:** Changed `python:3.10-slim` → `python:3.12-slim` and removed `apt-get install git` in template Dockerfile for compatibility with PyPI package (PEP 701 f-strings) and faster builds.
- [x] **#347 Docker API SyntaxError:** Fixed f-string nested quote `SyntaxError` in commands.py by installing from local source in tasker-agent Dockerfile and using Python 3.12 (PEP 701).
- [x] **#348 Neo4j schema warnings:** Removed typed relationship patterns (`:CONTAINS`, `:CODE_RELATIONSHIP`) and unused `f.language` from `get_stats` Cypher query to avoid planner warnings on empty graphs.
- [x] **#349 CLI help examples:** Added detailed epilog examples and workflow patterns to `--help` output for `issue create`, `issue list`, `dependency add`, and the main app.

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
| 1.0.3   | 2026-06-07 | Bugfix: status count (#414), --help pagination flags (#415), config path backslashes (#416) |
| 1.0.2   | 2026-05-29 | Bugfix: Emoji/traceback cleanup, --depends-on flag, non-TTY init, Docker local source, base image 3.12, Neo4j warnings, CLI help examples |
| 1.0.1   | 2026-05-25 | Bugfix: Schema init CypherSyntaxError & logger NameError |
| 1.0.0   | 2026-05-24 | Full Release — All issues resolved |
